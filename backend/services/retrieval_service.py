"""
Retrieval Service Module.

Why it is needed:
Bridges vector similarity search and LLM generation.
Formats retrieved document chunks into clean context blocks with explicit source headers,
and prepares structured citation metadata for the frontend.

Interview Concept:
Context formatting with metadata (Document Name, Page Number) serves a dual purpose:
1. Provides the LLM with clear document boundaries.
2. Enables precise source citation display in the user interface.
"""

from typing import List, Dict, Any
from langchain_core.documents import Document
from backend.vectorstore.faiss_store import faiss_store
from backend.services.llm_service import llm_service
from backend.config import settings

class RetrievalService:
    def format_context(self, chunks: List[Document]) -> str:
        """
        Formats retrieved Document chunks into a structured context string for the LLM prompt.
        """
        if not chunks:
            return ""

        context_blocks = []
        for idx, chunk in enumerate(chunks, 1):
            doc_name = chunk.metadata.get("document_name", chunk.metadata.get("source", "Unknown"))
            page_num = chunk.metadata.get("page", "N/A")
            header = f"[Source {idx}: {doc_name}, Page {page_num}]"
            context_blocks.append(f"{header}\n{chunk.page_content}")

        return "\n\n".join(context_blocks)

    def extract_sources(self, chunks: List[Document]) -> List[Dict[str, Any]]:
        """
        Extracts clean, deduplicated source citation objects from retrieved chunks.
        """
        sources = []
        seen = set()

        for chunk in chunks:
            doc_name = chunk.metadata.get("document_name", chunk.metadata.get("source", "Unknown"))
            page = chunk.metadata.get("page", 1)
            key = (doc_name, page)

            if key not in seen:
                seen.add(key)
                sources.append({
                    "document_name": doc_name,
                    "page": page,
                    "document_id": chunk.metadata.get("document_id", ""),
                    "department": chunk.metadata.get("department", "GENERAL")
                })

        return sources

    def answer_query(self, query: str, chunks: List[Document] = None, top_k: int = settings.DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Core RAG answer generation workflow:
        1. Accepts raw or authorized chunks (or performs vector search if none provided).
        2. Formats chunks into prompt context.
        3. Calls Groq LLM service.
        4. Returns structured result with answer, citations, and metadata.
        """
        if chunks is None:
            chunks = faiss_store.similarity_search(query, k=top_k)

        # Format context for LLM prompt
        formatted_context = self.format_context(chunks)

        # Call Groq LLM service
        answer = llm_service.generate_answer(question=query, context=formatted_context)

        # Extract source citations
        sources = self.extract_sources(chunks)

        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "retrieved_chunks_count": len(chunks),
            "chunks": [
                {
                    "content": c.page_content,
                    "metadata": c.metadata
                }
                for c in chunks
            ]
        }

# Global singleton retrieval service instance
retrieval_service = RetrievalService()
