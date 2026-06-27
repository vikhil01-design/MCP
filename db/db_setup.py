import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database credentials
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")


def get_connection_string(db_name=None):
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    if db_name:
        return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def execute_sql_file(conn, sql_file_path: Path):
    if not sql_file_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file_path.absolute()}")

    sql_script = sql_file_path.read_text(encoding="utf-8")
    raw_conn = conn.connection.driver_connection

    with raw_conn.cursor() as cur:
        cur.execute(sql_script)

    raw_conn.commit()


def setup_database():
    target_db = os.getenv("DB_NAME", "neondb")
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        engine = create_engine(database_url, isolation_level="AUTOCOMMIT")
    else:
        engine = create_engine(
            get_connection_string("postgres"), isolation_level="AUTOCOMMIT"
        )

    with engine.connect() as conn:
        logger.info(f"Connected to database host using target database {target_db}")

        if not database_url:
            result = conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{target_db}'")
            )
            if not result.fetchone():
                logger.info(f"Creating database {target_db}...")
                conn.execute(text(f"CREATE DATABASE {target_db}"))
            else:
                logger.info(f"Database {target_db} already exists.")

    engine = create_engine(get_connection_string(target_db))

    with engine.connect() as conn:
        logger.info("Ensuring pgvector extension and executing schema SQL...")

        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        sql_file_path = Path(__file__).resolve().parent / "legal_database_sample.sql"
        execute_sql_file(conn, sql_file_path)

        logger.info("Schema and sample data executed from legal_database_sample.sql")


if __name__ == "__main__":
    setup_database()
