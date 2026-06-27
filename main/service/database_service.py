import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = os.getenv("DATABASE_URL") or (
    f"postgresql://{DB_USER}:{DB_PASSWORD}" f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

_engine = None


def get_engine():
    """Lazy-load the database engine to avoid import-time dependency issues."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            echo=True,
            future=True,
        )
    return _engine


engine = None  # Placeholder for backward compatibility

logger = logging.getLogger(__name__)


def initialize_database():
    sql_file = Path("db/legal_database_sample.sql")

    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file.absolute()}")

    sql_script = sql_file.read_text(encoding="utf-8")

    conn_engine = get_engine()
    with conn_engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        # pgvector extension
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # execute entire schema + inserts
        raw_conn = conn.connection.driver_connection

        with raw_conn.cursor() as cur:
            cur.execute(sql_script)

        raw_conn.commit()

    logger.info("Database initialized successfully")
