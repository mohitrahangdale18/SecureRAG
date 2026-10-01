"""
Document Chunking Module.

Why it is needed:
Large documents cannot be embedded as single vectors efficiently, nor can they be passed entirely to an LLM.
Chunking splits document text into optimal segments (e.g., 600 characters with 100 overlap).

Interview Concept:
RecursiveCharacterTextSplitter is the industry standard chunker. It attempts to split text using paragraph breaks ("\n\n"),
line breaks ("\n"), sentence boundaries (". "), and word spaces (" "), avoiding mid-word cuts and preserving context.
Crucially, LangChain's splitter automatically propagates parent document metadata (tenant_id, allowed_roles, page) to all sub-chunks.
"""

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from backend.config import settings

def chunk_documents(
    documents: List[Document],
    chunk_size: int = settings.CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP
) -> List[Document]:
    """
    Splits a list of Documents into chunks while ensuring all security & source metadata is retained.
    """
    if not documents:
        return []

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = splitter.split_documents(documents)

    # Assign unique chunk_id metadata to each individual chunk for precise debugging and tracking
    for idx, chunk in enumerate(chunks):
        doc_id = chunk.metadata.get("document_id", "doc")
        page_num = chunk.metadata.get("page", 1)
        chunk.metadata["chunk_id"] = f"{doc_id}_p{page_num}_c{idx}"

    return chunks
