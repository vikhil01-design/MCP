import os

from dotenv import load_dotenv
from llama_index.core import SQLDatabase
from sqlalchemy import create_engine

load_dotenv()


def get_db_engine():
    """Create a SQLAlchemy engine for the configured Postgres database."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "password")
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        dbname = os.getenv("DB_NAME", "rag_db")
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

    return create_engine(database_url)


def get_sql_database(engine=None, include_tables=None):
    """
    Return a LlamaIndex SQLDatabase wrapper over the Postgres engine.

    By default it exposes the core business tables used in this demo.
    """
    if engine is None:
        engine = get_db_engine()
    if include_tables is None:
        include_tables = [
            "case_law_metadata",
            "contract_clause_index",
            "legal_acts_reference",
            "document_metadata",
        ]
    return SQLDatabase(engine, include_tables=include_tables)
