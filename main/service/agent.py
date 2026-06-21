import logging
import os
from dotenv import load_dotenv
from llama_index.core.agent.workflow.multi_agent_workflow import AgentWorkflow
from llama_index.core import Settings
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding

from main.service.tools import get_sql_tool, get_vector_tool
from .mcp_client import LegalMCPService

load_dotenv()


# Global agent instance (initialized once)
_agent = None


async def get_agent():
    """Get or create the OpenAI agent with SQL and Vector tools."""
    global _agent

    if _agent is None:
        # Initialize LLM
        llm = AzureOpenAI(
            model=os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT"),
            deployment_name=os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
        Settings.llm = llm

        # Initialize embeddings
        embed_model = AzureOpenAIEmbedding(
            model=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            deployment_name=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        )
        Settings.embed_model = embed_model

        # Prepare Tools
        sql_tool = get_sql_tool()
        vector_tool = get_vector_tool()
        mcp_service = LegalMCPService()
        mcp_tools = await mcp_service.load_tools(allowed_tools=None)

        if not isinstance(mcp_tools, list):
            mcp_tools = [mcp_tools]

        logging.info(f"Loaded {len(mcp_tools)} MCP tools")
        tools = [sql_tool, vector_tool, *mcp_tools]
        logging.info(f"Creating agent workflow with {len(tools)} tools")

        # Create Agent Workflow
        _agent = AgentWorkflow.from_tools_or_functions(
            tools,
            llm=llm,
            verbose=True,
            system_prompt="""
            You are an intelligent business assistant with access to three tool categories:
            1) Legal_database for our internal SQL business data,
            2) company_documents for internal document search,
            3) MCP tools for external legal research and third-party knowledge.

            Guidelines:
            - Prefer 'Legal_database' for any question about our internal data, records, metrics, pricing, revenue, counts, or database facts.
            - Prefer 'company_documents' for internal documents, policies, strategies, goals, descriptions, or anything that should come from our own documents.
            - Only use MCP tools when the user explicitly asks for external legal research, statutes, case law, or knowledge beyond what is available inside our internal data and documents.
            - Do not use MCP tools to answer questions that can be satisfied by the SQL database or internal documents.
            - If a question involves both internal data and external legal knowledge, use the appropriate internal tool(s) first and then consult MCP tools only for the external portion.
            - Always explain your reasoning when choosing tools.
            - Be concise but comprehensive.
            """,
        )

    return _agent
