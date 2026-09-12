import os
import sqlite3

from pathlib import Path
from dotenv import load_dotenv

import psycopg

from google import genai
from google.genai import types

from pgvector.psycopg import register_vector


# =========================================================
# ENV
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


DATABASE_URL = os.getenv("DATABASE_URL")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

EMBED_MODEL = os.getenv(
    "EMBED_MODEL",
    "gemini-embedding-2"
)


# =========================================================
# GEMINI CLIENT
# =========================================================

ai_client = genai.Client(
    api_key=GEMINI_API_KEY
)


def get_embedding(text):

    response = ai_client.models.embed_content(

        model=EMBED_MODEL,

        contents=text,

        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    return response.embeddings[0].values


# =========================================================
# CONNECT TO POSTGRES
# =========================================================

print("Connecting to PostgreSQL...")

conn = psycopg.connect(
    DATABASE_URL
)

conn.autocommit = True

cursor = conn.cursor()


# =========================================================
# ENABLE PGVECTOR
# =========================================================

cursor.execute(
    "CREATE EXTENSION IF NOT EXISTS vector;"
)

print("pgvector enabled")


# pgvector Python support
register_vector(conn)


# =========================================================
# CREATE PRODUCTS TABLE
# =========================================================

cursor.execute("""
CREATE TABLE IF NOT EXISTS products(

    id BIGSERIAL PRIMARY KEY,

    type TEXT,

    title TEXT NOT NULL,

    sub TEXT,

    model TEXT,

    price TEXT,

    emi TEXT,

    image TEXT,

    embedding VECTOR(768)

);
""")

print("Products table created")


# =========================================================
# READ EXISTING SQLITE PRODUCTS
# =========================================================

sqlite_path = BASE_DIR / "dell.db"


if not sqlite_path.exists():

    print("dell.db not found")

    cursor.close()
    conn.close()

    raise SystemExit


sqlite_conn = sqlite3.connect(
    sqlite_path
)

sqlite_conn.row_factory = sqlite3.Row

sqlite_cursor = sqlite_conn.cursor()


sqlite_cursor.execute("""
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
""")


products = sqlite_cursor.fetchall()


print(
    "SQLite products found:",
    len(products)
)


# =========================================================
# MIGRATE PRODUCTS
# =========================================================

for product in products:

    text = f"""
Product: {product["title"]}
Description: {product["sub"]}
Model: {product["model"] or ""}
Type: {product["type"] or ""}
Price: {product["price"]}
EMI: {product["emi"] or ""}
"""


    print(
        "Creating embedding:",
        product["model"] or product["title"]
    )


    embedding = get_embedding(
        text
    )


    cursor.execute("""
        INSERT INTO products
        (
            id,
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
            %s,%s,%s,%s,%s,%s,%s,%s,%s
        )

        ON CONFLICT(id)

        DO UPDATE SET

            type=EXCLUDED.type,

            title=EXCLUDED.title,

            sub=EXCLUDED.sub,

            model=EXCLUDED.model,

            price=EXCLUDED.price,

            emi=EXCLUDED.emi,

            image=EXCLUDED.image,

            embedding=EXCLUDED.embedding

    """, (

        product["id"],

        product["type"],

        product["title"],

        product["sub"],

        product["model"],

        product["price"],

        product["emi"],

        product["image"],

        embedding

    ))


    print(
        "Migrated:",
        product["model"]
        or product["title"]
    )


# =========================================================
# RESET ID SEQUENCE
# =========================================================

cursor.execute("""
SELECT setval(
    pg_get_serial_sequence(
        'products',
        'id'
    ),

    COALESCE(
        (
            SELECT MAX(id)
            FROM products
        ),
        1
    ),

    true
);
""")


# =========================================================
# VERIFY
# =========================================================

cursor.execute("""
SELECT
    id,
    title,
    model,
    price

FROM products

ORDER BY id
""")


rows = cursor.fetchall()


print("\nPOSTGRES PRODUCTS:")


for row in rows:

    print(row)


# =========================================================
# CLOSE CONNECTIONS
# =========================================================

sqlite_cursor.close()

sqlite_conn.close()

cursor.close()

conn.close()


print("\nMIGRATION COMPLETE ✅")