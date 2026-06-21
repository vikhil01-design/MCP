"""
Query Service - Handles hybrid agent queries and tool tracking
"""

import logging
from typing import Optional, List, Dict, Any

from main.service.agent import get_agent

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QueryResult:
    """Result of a hybrid query with tool tracking"""

    def __init__(
        self, question: str, answer: str, tools_used: Optional[List[str]] = None
    ):
        self.question = question
        self.answer = answer
        self.tools_used = tools_used or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        sources_description = None
        if self.tools_used:
            sources_description = f"Agent used: {', '.join(self.tools_used)}"
        else:
            sources_description = "Agent reasoning without external tools"

        return {
            "question": self.question,
            "answer": self.answer,
            "tools_used": self.tools_used if self.tools_used else None,
            "sources_used": sources_description,
        }


async def execute_hybrid_query(question: str) -> QueryResult:
    """
    Execute a hybrid agentic query that can use SQL database, vector store, or both.

    Args:
        question: The user's question

    Returns:
        QueryResult with answer and tools used

    Raises:
        Exception: If query execution fails
    """
    logger.info(f"Executing hybrid query: {question}")

    # Get the agent and execute the query via workflow run
    agent = await get_agent()
    handler = agent.run(question)
    response = await handler

    # Extract tools used from the agent's response
    tools_used = _extract_tools_used(agent, response)

    logger.info(f"Query completed. Tools used: {tools_used}")

    return QueryResult(
        question=question,
        answer=str(response),
        tools_used=tools_used,
    )


def _extract_tools_used(agent, response) -> List[str]:
    """
    Extract which tools the agent used during query execution.

    Args:
        agent: The OpenAI agent instance
        response: The agent's response object

    Returns:
        List of tool names used (e.g., ['SQL Database (sales_database)', 'Vector Store (company_documents)'])
    """
    tools_used = []

    # Method 1: Try to extract from response sources
    if hasattr(response, "sources") and response.sources:
        for source in response.sources:
            if hasattr(source, "tool_name"):
                tool_name = source.tool_name
                if tool_name not in tools_used:
                    tools_used.append(tool_name)

    # Method 2: Extract tool calls directly from the response object
    if not tools_used and hasattr(response, "tool_calls"):
        for call in response.tool_calls:
            if hasattr(call, "tool_name"):
                tool_name = call.tool_name
            elif isinstance(call, dict):
                tool_name = call.get("tool_name") or call.get("function", {}).get(
                    "name", ""
                )
            else:
                tool_name = None

            friendly_name = _map_tool_name(tool_name) if tool_name else None
            if friendly_name and friendly_name not in tools_used:
                tools_used.append(friendly_name)

    # Method 3: Check chat history for tool calls (more reliable for OpenAI agents)
    if not tools_used and hasattr(agent, "chat_history"):
        for msg in agent.chat_history:
            if hasattr(msg, "additional_kwargs"):
                tool_calls = msg.additional_kwargs.get("tool_calls", [])
                for call in tool_calls:
                    if isinstance(call, dict) and "function" in call:
                        func_name = call["function"].get("name", "")
                        friendly_name = _map_tool_name(func_name)
                        if friendly_name and friendly_name not in tools_used:
                            tools_used.append(friendly_name)

    return tools_used


def _map_tool_name(internal_name: str) -> Optional[str]:
    """
    Map internal tool function names to user-friendly names.

    Args:
        internal_name: Internal function/tool name from the agent

    Returns:
        User-friendly tool name or None if not recognized
    """
    # Map internal names to friendly names
    if "sales_database" in internal_name or internal_name == "sales_database":
        return "SQL Database (sales_database)"
    elif "company_documents" in internal_name or internal_name == "company_documents":
        return "Vector Store (company_documents)"
    else:
        # Return the original name if we don't have a mapping
        return internal_name if internal_name else None
