"""
Document Ingestion Module.

Why it is needed:
Raw PDF files cannot be fed directly into an LLM or Vector Store.
This module extracts readable text page-by-page from a PDF file and attaches essential metadata 
including tenant identity, target department, permitted roles, and page numbers.

Interview Concept:
Metadata enrichment at ingestion time is what enables downstream permission filtering in SecureRAG.
Without attaching tenant_id and allowed_roles to each page/chunk, security cannot be enforced during vector retrieval.
"""

from typing import List, Dict, Any
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

def load_pdf_document(
    file_path: str,
    doc_metadata: Dict[str, Any]
) -> List[Document]:
    """
    Extracts text page-by-page from a PDF file and enriches each page Document with tenant and role metadata.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    loader = PyPDFLoader(str(path))
    pages = loader.load()

    if not pages:
        raise ValueError(f"PDF at '{file_path}' contains no extractable text or pages.")

    enriched_documents = []
    for idx, page in enumerate(pages):
        text = page.page_content.strip()
        if not text:
            continue  # Skip completely empty pages
            
        # PyPDFLoader returns zero-indexed page in metadata. Convert to 1-indexed for human readability.
        raw_page = page.metadata.get("page", idx)
        page_num = raw_page + 1 if isinstance(raw_page, int) else raw_page

        combined_metadata = {
            "tenant_id": doc_metadata.get("tenant_id", "default"),
            "document_id": doc_metadata.get("document_id", path.stem),
            "document_name": doc_metadata.get("document_name", path.name),
            "department": doc_metadata.get("department", "GENERAL"),
            "allowed_roles": doc_metadata.get("allowed_roles", ["ADMIN"]),
            "page": page_num,
            "source": path.name
        }

        enriched_documents.append(
            Document(page_content=text, metadata=combined_metadata)
        )

    if not enriched_documents:
        raise ValueError(f"PDF '{path.name}' contained pages, but no readable text could be extracted.")

    return enriched_documents
