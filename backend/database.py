import os
import psycopg

from pathlib import Path
from dotenv import load_dotenv

from psycopg.rows import dict_row

from pgvector import Vector
from pgvector.psycopg import register_vector


BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


def get_connection():

    conn = psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )

    register_vector(conn)

    return conn


def create_table():

    conn = psycopg.connect(
        DATABASE_URL
    )

    cursor = conn.cursor()


    cursor.execute("""
        CREATE EXTENSION IF NOT EXISTS vector;
    """)


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


    conn.commit()

    cursor.close()
    conn.close()


def search_similar_products(
    embedding,
    limit=2
):

    conn = get_connection()

    cursor = conn.cursor()


    # Python list → pgvector Vector
    query_vector = Vector(
        embedding
    )


    cursor.execute("""
        SELECT

            id,
            type,
            title,
            sub,
            model,
            price,
            emi,
            image,

            embedding <=> %s AS distance

        FROM products

        WHERE embedding IS NOT NULL

        ORDER BY distance

        LIMIT %s

    """, (

        query_vector,
        limit

    ))


    products = cursor.fetchall()


    cursor.close()
    conn.close()


    return products