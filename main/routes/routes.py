"""
Routes Module
FastAPI route handlers for document upload and querying.
"""

import os
import re
import logging
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from ..service.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()
rag_service = RAGService()

MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_QUERY_LENGTH = 2000
MIN_SIMILARITY_TOP_K = 1
MAX_SIMILARITY_TOP_K = 20
ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.md', '.docx'}



class UploadResponse(BaseModel):
    """Response model for upload endpoint."""
    message: str
    documents_indexed: int


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Sprint 9 Practice RAG API"}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other security issues."""
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    filename = os.path.basename(filename)
    filename = filename.replace('/', '_').replace('\\', '_')
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    return filename


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload and process a PDF document.
    Args:
        file: PDF file to upload and process (max 10MB)
        
    Returns:
        Processing result with document count
    """

    logger.info(f"Received upload request: {file.filename}")

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    temp_path = None
    
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        allowed_extensions = [".pdf", ".txt", ".md", ".docx"]

        if not any(
            file.filename.lower().endswith(ext)
            for ext in allowed_extensions
        ):
            logger.error(
                f"Unsupported file type uploaded: {file.filename}"
            )

            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Allowed types: .pdf, .txt, .md."
            )

        contents = await file.read()
        
        if len(contents) > MAX_FILE_SIZE:

            logger.warning(
                f"File exceeds max size: {file.filename}"
            )

            raise HTTPException(
                status_code=400,
                detail="File size exceeds maximum limit of 10MB"
            )
        
        suffix = Path(file.filename).suffix

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(contents)
            temp_path = temp_file.name

        logger.info(f"Temporary file created: {temp_path}")
        
        result = rag_service.process_document(
            pdf_path=temp_path,
            original_filename=file.filename
        )

        logger.info(
            f"Document processed successfully: {file.filename}"
        )

        return UploadResponse(
            message=result.get(
                "message",
                "Document uploaded successfully"
            ),
            documents_indexed=result.get(
                "documents_indexed",
                0
            )
        )

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Error processing upload: {str(e)}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

    finally:
        # ---------------------------------------------------------
        # Cleanup temporary file
        # ---------------------------------------------------------
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
                logger.info(
                    f"Temporary file removed: {temp_path}"
                )
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to remove temp file: {cleanup_error}"
                )


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Sprint 9 Practice RAG API",
        "version": "1.0.0",
        "endpoints": {
            "POST /upload": "Upload documents for indexing",
            "POST /query": "Query the RAG system",
            "GET /health": "Health check"
        }
    }
