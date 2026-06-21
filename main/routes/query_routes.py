from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

from main.service.query_service import execute_hybrid_query

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(
        ..., description="The question to ask the agent", min_length=1
    )

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is our refund policy for annual subscriptions?"
            }
        }


class QueryResponse(BaseModel):
    question: str
    answer: str
    tools_used: Optional[List[str]] = None
    sources_used: Optional[str] = None


@router.post("/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Query the Agentic RAG system with a question.

    The agent will automatically decide whether to:
    - Query the SQL database (for pricing, revenue, customer data)
    - Search vector documents (for policies, strategies, goals)
    - Use both sources and synthesize the answer

    Returns the answer along with which tools were used.
    """
    try:
        # Execute hybrid query using the service layer
        result = await execute_hybrid_query(request.question)

        # Convert to response model
        return QueryResponse(**result.to_dict())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
