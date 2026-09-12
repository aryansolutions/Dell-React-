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


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

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
).rstrip("/")


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
    "http://127.0.0.1:5173",

    # Production Vercel frontend
    "https://dell-react.vercel.app"
]


# Add environment frontend URL too
if FRONTEND_URL and FRONTEND_URL not in allowed_origins:
    allowed_origins.append(FRONTEND_URL)


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
# PRODUCT TEXT FOR EMBEDDING
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
        "message": "Timeus AI backend is running",
        "database": "PostgreSQL + pgvector",
        "chat_model": CHAT_MODEL,
        "embedding_model": EMBED_MODEL
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "ok"
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
# Keep before /products/{product_id}
# =========================================================

@app.get("/products/search/")
def search_products(q: str):

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
def get_product(product_id: int):

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
def add_product(product: Product):

    text = product_to_text(product)


    try:

        embedding = get_embedding(text)

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Embedding failed: {e}"
        )


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
        "message": "Product added",
        "id": new_id
    }


# =========================================================
# UPDATE PRODUCT
# =========================================================

@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    product: Product
):

    text = product_to_text(product)


    try:

        embedding = get_embedding(text)

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
        "message": "Product updated"
    }


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.delete("/products/{product_id}")
def delete_product(product_id: int):

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
        "message": "Product deleted"
    }


# =========================================================
# NORMAL PRODUCT CHAT
# Sends all products to Gemini
# =========================================================

@app.post("/product-chat")
def product_chat(data: ChatRequest):

    message = data.message.strip()


    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )


    # Simple greetings should not trigger product recommendations
    if message.lower() in {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "hello there"
    }:

        return {
            "response":
                "Hi! What kind of Dell product are you looking for?"
        }


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
- Reply naturally.
- Keep replies to 1-3 short sentences.
- Do not recommend anything unless the user asks for a product or describes a need.
- Do not mention context, retrieval, database, embeddings or internal systems.
- Do not invent specifications.
- Do not invent products.
- Do not say "model not specified".
- If the question is vague, ask one short follow-up question.
- When recommending a product, mention its name, price and one short reason.
- Only use information given below.

PRODUCTS:

{context}

USER:

{message}

ANSWER:
"""


    ai_response = ask_gemini(prompt)


    return {
        "response": ai_response
    }


# =========================================================
# RAG CHAT
#
# User question
#      ↓
# Gemini embedding
#      ↓
# PostgreSQL + pgvector
#      ↓
# Relevant products
#      ↓
# Gemini
#      ↓
# React
# =========================================================

@app.post("/rag-chat")
def rag_chat(data: ChatRequest):

    message = data.message.strip()


    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )


    # -----------------------------------------------------
    # Handle greetings WITHOUT running vector search
    # -----------------------------------------------------

    if message.lower() in {
        "hi",
        "hello",
        "hey",
        "hii",
        "hiii",
        "hello there"
    }:

        return {
            "response":
                "Hi! What kind of Dell product are you looking for?",

            "products": [],

            "retrieved_products": []
        }


    # -----------------------------------------------------
    # 1. Embed user question
    # -----------------------------------------------------

    try:

        question_embedding = get_embedding(message)

    except Exception as e:

        raise HTTPException(
            status_code=503,
            detail=f"Embedding failed: {e}"
        )


    # -----------------------------------------------------
    # 2. pgvector semantic search
    # -----------------------------------------------------

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

            "products": [],

            "retrieved_products": []
        }


    # -----------------------------------------------------
    # 3. Build Gemini context
    # -----------------------------------------------------

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


    # -----------------------------------------------------
    # 4. Ask Gemini
    # -----------------------------------------------------

    prompt = f"""
You are a concise Dell shopping assistant.

Use ONLY the products supplied below.

PRODUCTS:

{context}

USER:

{message}

RULES:

- Answer in 1-3 short sentences.
- Be natural and direct.
- Never mention vector search, retrieval, context, embeddings or database.
- Never invent products.
- Never invent specifications.
- If one product clearly matches, recommend only that product.
- Mention price only when useful.
- Give one short reason for the recommendation.
- If neither product really satisfies the request, say that briefly.
- Do not create unnecessary bullet lists.
- Do not repeat the user's question.
- Do not use phrases like "based on the retrieved products".
- Do not say "model not specified".

ANSWER:
"""


    ai_response = ask_gemini(prompt)


    # -----------------------------------------------------
    # 5. Format products for React
    # -----------------------------------------------------

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
                    float(product["distance"]),
                    4
                )
        })


    # IMPORTANT:
    # React currently reads data.products
    #
    # retrieved_products is also returned so Swagger/API
    # still clearly shows what RAG retrieved.

    return {

        "response":
            ai_response,

        "products":
            retrieved_products,

        "retrieved_products":
            retrieved_products
    }