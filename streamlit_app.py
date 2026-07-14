import asyncio
import logging
import os
import tempfile
from pathlib import Path

import streamlit as st

logger = logging.getLogger(__name__)

st.set_page_config(page_title="LegalDoc Navigator", page_icon="⚖️", layout="centered")

APP_TITLE = "LegalDoc Navigator"
APP_SUBTITLE = "Ask questions about your legal documents"


def initialize_services() -> None:
    """Initialize the shared RAG service if possible."""
    from main.routes.routes import rag_service
    from main.service.database_service import initialize_database

    if st.session_state.get("services_initialized"):
        return

    try:
        initialize_database()
        rag_service.initialize()
        st.session_state.services_initialized = True
        st.session_state.service_status = "ready"
    except Exception as exc:
        st.session_state.services_initialized = False
        st.session_state.service_status = "warning"
        st.session_state.service_message = (
            "Some services are not configured yet. The app may still start, but full functionality depends on Azure, Qdrant, and database settings. "
            f"Error: {exc}"
        )


def upload_document(uploaded_file) -> None:
    """Upload a document to the RAG pipeline for indexing."""
    from main.routes.routes import rag_service

    if uploaded_file is None:
        st.warning("Please choose a document first.")
        return

    suffix = Path(uploaded_file.name).suffix or ".pdf"
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_path = temp_file.name

        with st.spinner("Processing document..."):
            result = rag_service.process_document(
                pdf_path=temp_path,
                original_filename=uploaded_file.name,
            )

        st.session_state.last_upload_result = result
        st.success("Document uploaded and indexed successfully.")
    except Exception as exc:
        st.error(f"Upload failed: {exc}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                logger.warning(
                    "Temporary upload file could not be removed: %s", temp_path
                )


def run_query(question: str):
    """Run the existing hybrid query workflow."""
    from main.service.query_service import execute_hybrid_query

    return asyncio.run(execute_hybrid_query(question))


def render_app() -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    initialize_services()

    if st.session_state.get("service_status") == "warning":
        st.warning(st.session_state.get("service_message", "Service status unknown."))

    st.subheader("Upload a document")
    uploaded_file = st.file_uploader(
        "Choose a PDF, text, markdown, or Word document",
        type=["pdf", "txt", "md", "docx"],
    )
    if st.button("Upload and index", use_container_width=True):
        upload_document(uploaded_file)

    st.divider()

    st.subheader("Ask a question")
    question = st.text_area(
        "Question",
        placeholder="Example: Summarize the termination clause in this contract",
        height=120,
    )
    if st.button("Get answer", use_container_width=True):
        if not question.strip():
            st.warning("Please enter a question first.")
            return

        with st.spinner("Thinking..."):
            try:
                result = run_query(question)
                st.session_state.last_query_result = result
            except Exception as exc:
                st.error(f"Query failed: {exc}")
                return

        st.markdown("### Answer")
        st.write(result.answer)

        if getattr(result, "tools_used", None):
            st.markdown("### Tools used")
            st.write(result.tools_used)

        if getattr(result, "sources_used", None):
            st.markdown("### Sources")
            st.write(result.sources_used)


def main() -> None:
    render_app()


if __name__ == "__main__":
    main()
