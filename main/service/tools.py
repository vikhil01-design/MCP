"""
Tools Module - Provides SQL and Vector tools for the agentic RAG system
"""

import os
import logging

from llama_index.core import Document, StorageContext, VectorStoreIndex, Settings
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.tools import QueryEngineTool
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.ingestion import IngestionPipeline
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

from .rag_service import create_vector_store
from .sql_database import get_sql_database

# Load vector index from the RAG service instance
from ..routes.routes import rag_service

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# ----- Public API: Tool Creation -----


def get_vector_tool():
    """
    Create a QueryEngineTool for querying company documents stored in pgvector.

    Returns:
        QueryEngineTool configured for vector document search
    """
    logger.info("Creating vector tool...")

    # Initialize Azure embeddings if not already set
    if Settings._embed_model is None:
        logger.info("Initializing Azure OpenAI embeddings...")
        embed_model = AzureOpenAIEmbedding(
            model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            deployment_name=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
        Settings.embed_model = embed_model

    if not rag_service._index_loaded:
        rag_service._load_existing_index()

    vector_index = rag_service.index

    if vector_index is None:
        raise RuntimeError(
            "No vector index found in the RAG service. Please upload documents first via /api/upload"
        )

    query_engine = vector_index.as_query_engine()

    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="company_documents",
        description=(
            "Contains strategy docs, policies, meeting notes, "
            "refund policies, and business goals."
        ),
    )


def get_sql_tool():
    """
    Create a QueryEngineTool for querying the SQL business database.

    Returns:
        QueryEngineTool configured for SQL database queries
    """
    logger.info("Creating SQL tool...")

    # Get SQL database and create query engine
    sql_database = get_sql_database()
    query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=[
            "case_law_metadata",
            "contract_clause_index",
            "legal_acts_reference",
            "document_metadata",
        ],
        verbose=True,
    )

    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="Legal_database",
        description=(
            "Contains sales transactions, customer data, revenue metrics, "
            "tier pricing, discounts, and taxes."
        ),
    )
