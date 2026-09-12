import os

from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    get_connection,
    create_table,
    search_similar_products
)


# =========================================================
# ENVIRONMENT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

CHAT_MODEL = os.getenv(
    "CHAT_MODEL",
    "gemini-3.6-flash"
)

EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "gemini-embedding-2"
)

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    ""
)


# =========================================================
# GEMINI
# =========================================================

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)


def get_embedding(text):

    response = gemini_client.models.embed_content(

        model=EMBED_MODEL,

        contents=text,

        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    return response.embeddings[0].values


def ask_gemini(prompt):

    try:

        response = gemini_client.models.generate_content(
            model=CHAT_MODEL,
            contents=prompt
        )

        return (
            response.text
            or "No AI response received."
        )

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Gemini error: {e}"
        )


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Timeus AI Shopping API",
    version="2.0.0"
)


# =========================================================
# CORS
# =========================================================

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]


if FRONTEND_URL:

    allowed_origins.append(
        FRONTEND_URL
    )


app.add_middleware(

    CORSMiddleware,

    allow_origins=allowed_origins,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"]

)


# =========================================================
# CREATE DATABASE TABLE
# =========================================================

create_table()


# =========================================================
# PYDANTIC MODELS
# =========================================================

class Product(BaseModel):

    type: str | None = None

    title: str

    sub: str

    model: str | None = None

    price: str

    emi: str | None = None

    image: str


class ChatRequest(BaseModel):

    message: str


# =========================================================
# CREATE PRODUCT TEXT FOR EMBEDDING
# =========================================================

def product_to_text(product):

    return f"""
Product: {product.title}
Description: {product.sub}
Model: {product.model or ""}
Type: {product.type or ""}
Price: {product.price}
EMI: {product.emi or ""}
"""


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    return {

        "message":
            "Timeus AI backend is running",

        "database":
            "PostgreSQL + pgvector",

        "chat_model":
            CHAT_MODEL,

        "embedding_model":
            EMBED_MODEL
    }


# =========================================================
# GET ALL PRODUCTS
# =========================================================

@app.get("/products")
def get_products():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            id,
            type,
            title,
            sub,
            model,
            price,
            emi,
            image

        FROM products

        ORDER BY id
    """)


    products = cursor.fetchall()


    cursor.close()

    conn.close()


    return products


# =========================================================
# SEARCH PRODUCTS
#
# IMPORTANT:
# Keep above /products/{product_id}
# =========================================================

@app.get("/products/search/")
def search_products(
    q: str
):

    conn = get_connection()

    cursor = conn.cursor()


    search = f"%{q}%"


    cursor.execute("""
        SELECT
            id,
            type,
            title,
            sub,
            model,
            price,
            emi,
            image

        FROM products

        WHERE title ILIKE %s
           OR sub ILIKE %s
           OR model ILIKE %s
           OR type ILIKE %s

        ORDER BY id

    """, (

        search,
        search,
        search,
        search

    ))


    products = cursor.fetchall()


    cursor.close()

    conn.close()


    return products


# =========================================================
# GET ONE PRODUCT
# =========================================================

@app.get("/products/{product_id}")
def get_product(
    product_id: int
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            id,
            type,
            title,
            sub,
            model,
            price,
            emi,
            image

        FROM products

        WHERE id=%s

    """, (

        product_id,

    ))


    product = cursor.fetchone()


    cursor.close()

    conn.close()


    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    return product


# =========================================================
# ADD PRODUCT
# =========================================================

@app.post("/products")
def add_product(
    product: Product
):

    # -----------------------------------
    # Create embedding
    # -----------------------------------

    text = product_to_text(
        product
    )


    try:

        embedding = get_embedding(
            text
        )

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Embedding failed: {e}"
        )


    # -----------------------------------
    # Save to PostgreSQL
    # -----------------------------------

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        INSERT INTO products
        (
            type,
            title,
            sub,
            model,
            price,
            emi,
            image,
            embedding
        )

        VALUES(
            %s,%s,%s,%s,%s,%s,%s,%s
        )

        RETURNING id

    """, (

        product.type,

        product.title,

        product.sub,

        product.model,

        product.price,

        product.emi,

        product.image,

        embedding

    ))


    new_product = cursor.fetchone()

    new_id = new_product["id"]


    conn.commit()


    cursor.close()

    conn.close()


    return {

        "message":
            "Product added",

        "id":
            new_id
    }


# =========================================================
# UPDATE PRODUCT
# =========================================================

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: Product
):

    # New product information means
    # embedding should also be regenerated.

    text = product_to_text(
        product
    )


    try:

        embedding = get_embedding(
            text
        )

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Embedding failed: {e}"
        )


    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        UPDATE products

        SET
            type=%s,
            title=%s,
            sub=%s,
            model=%s,
            price=%s,
            emi=%s,
            image=%s,
            embedding=%s

        WHERE id=%s

    """, (

        product.type,

        product.title,

        product.sub,

        product.model,

        product.price,

        product.emi,

        product.image,

        embedding,

        product_id

    ))


    updated = cursor.rowcount


    conn.commit()


    cursor.close()

    conn.close()


    if updated == 0:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    return {

        "message":
            "Product updated"
    }


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        DELETE FROM products
        WHERE id=%s
    """, (

        product_id,

    ))


    deleted = cursor.rowcount


    conn.commit()


    cursor.close()

    conn.close()


    if deleted == 0:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )


    return {

        "message":
            "Product deleted"
    }


# =========================================================
# NORMAL PRODUCT CHAT
#
# Sends ALL products to Gemini.
# Useful for comparing normal prompting vs RAG.
# =========================================================

@app.post("/product-chat")
def product_chat(
    data: ChatRequest
):

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            id,
            type,
            title,
            sub,
            model,
            price,
            emi

        FROM products

        ORDER BY id
    """)


    products = cursor.fetchall()


    cursor.close()

    conn.close()


    context = ""


    for product in products:

        context += f"""
ID: {product["id"]}
Type: {product["type"]}
Title: {product["title"]}
Description: {product["sub"]}
Model: {product["model"]}
Price: {product["price"]}
EMI: {product["emi"]}
-------------------
"""


    prompt = f"""
You are a concise Dell shopping assistant.

Rules:
- Keep replies very short: usually 1-3 sentences.
- If the user only says hello/hi/hey, greet them and ask what they are looking for.
- Do NOT recommend a product unless the user asks for a recommendation or gives a need.
- Do NOT mention "retrieved products", "context", "available items", or internal system details.
- Do NOT say things like "model not specified".
- Do NOT repeat unnecessary information.
- Do NOT use long bullet lists unless the user explicitly asks for options.
- If recommending a product, mention only:
  product name, price, and one short reason.
- If the request is vague, ask one short follow-up question.
- Only use products provided in the context.
- Never invent product details.

Product context:
{context}

User:
{message}

Reply naturally and concisely.
"""


    ai_response = ask_gemini(
        prompt
    )


    return {

        "response":
            ai_response
    }


# =========================================================
# RAG CHAT
#
# Question
#      ↓
# Gemini embedding
#      ↓
# PostgreSQL pgvector
#      ↓
# Top products
#      ↓
# Gemini
#      ↓
# Answer
# =========================================================

@app.post("/rag-chat")
def rag_chat(
    data: ChatRequest
):

    message = data.message.strip()


    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )


    # -----------------------------------
    # 1. Embed user question
    # -----------------------------------

    try:

        question_embedding = get_embedding(
            message
        )

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Embedding failed: {e}"
        )


    # -----------------------------------
    # 2. pgvector similarity search
    # -----------------------------------

    try:

        products = search_similar_products(
            question_embedding,
            limit=2
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Vector search failed: {e}"
        )


    if not products:

        return {

            "response":
                "I couldn't find a matching product.",

            "retrieved_products":
                []
        }


    # -----------------------------------
    # 3. Build context
    # -----------------------------------

    context = ""


    for product in products:

        context += f"""
Product: {product["title"]}
Description: {product["sub"]}
Model: {product["model"]}
Type: {product["type"]}
Price: {product["price"]}
EMI: {product["emi"]}
-------------------
"""


    # -----------------------------------
    # 4. Ask Gemini
    # -----------------------------------

    prompt = f"""
You are an AI shopping assistant.

A semantic vector search has already
retrieved the most relevant products.

Use ONLY the products below.

RETRIEVED PRODUCTS:

{context}

USER QUESTION:

{message}

RULES:

1. Recommend the best matching product.

2. Do not invent products.

3. Do not invent specifications.

4. Explain briefly why it matches.

5. Mention model and price when available.

6. If the products do not actually satisfy
the user's request, say so clearly.

7. Keep the response concise and natural.
"""


    ai_response = ask_gemini(
        prompt
    )


    # -----------------------------------
    # 5. Format products for React
    # -----------------------------------

    retrieved_products = []


    for product in products:

        retrieved_products.append({

            "id":
                product["id"],

            "title":
                product["title"],

            "model":
                product["model"],

            "description":
                product["sub"],

            "price":
                product["price"],

            "distance":
                round(
                    float(
                        product["distance"]
                    ),
                    4
                )
        })


    return {

        "response":
            ai_response,

        "retrieved_products":
            retrieved_products
    }