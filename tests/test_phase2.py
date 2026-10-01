"""
Test Script for Phase 2: RAG Retrieval -> Grounded Prompt Construction -> Fallback Behavior.

Verifies:
1. Context formatting with source tags.
2. Source citation extraction.
3. Fallback answer ("I couldn't find this information in the authorized documents.") when context is empty.
"""

import pytest
from langchain_core.documents import Document
from backend.services.retrieval_service import retrieval_service
from backend.services.llm_service import llm_service

def test_context_formatting_and_citation_extraction():
    """Tests that chunks are converted into structured context and source citations."""
    sample_chunks = [
        Document(
            page_content="Employees receive 18 annual paid leave days.",
            metadata={"document_name": "employee_policy.pdf", "page": 4, "document_id": "hr_001"}
        ),
        Document(
            page_content="Sick leave is capped at 10 paid days per calendar year.",
            metadata={"document_name": "employee_policy.pdf", "page": 5, "document_id": "hr_001"}
        )
    ]

    formatted_context = retrieval_service.format_context(sample_chunks)
    assert "[Source 1: employee_policy.pdf, Page 4]" in formatted_context
    assert "18 annual paid leave days" in formatted_context

    sources = retrieval_service.extract_sources(sample_chunks)
    assert len(sources) == 2
    assert sources[0]["document_name"] == "employee_policy.pdf"
    assert sources[0]["page"] == 4

def test_empty_context_fallback():
    """Verifies that empty context immediately triggers the strict zero-hallucination fallback."""
    answer = llm_service.generate_answer("What is the annual leave policy?", context="")
    assert answer == "I couldn't find this information in the authorized documents."

def test_retrieval_service_with_empty_chunks():
    """Verifies retrieval service response format when no chunks match."""
    result = retrieval_service.answer_query("Non-existent policy topic?", chunks=[])
    assert result["answer"] == "I couldn't find this information in the authorized documents."
    assert result["sources"] == []
    assert result["retrieved_chunks_count"] == 0
