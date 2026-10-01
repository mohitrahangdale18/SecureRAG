"""
Chat & Question Answering Router.
"""

from fastapi import APIRouter, HTTPException
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.schemas.user import UserContext
from backend.rag.retriever import permission_aware_retriever
from backend.services.retrieval_service import retrieval_service
from backend.services.audit_service import audit_service

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Permission-Aware RAG Chat Endpoint:
    1. Validates user context (user_id, tenant_id, role).
    2. Performs vector similarity search with permission filtering.
    3. Formats authorized context into strict prompt.
    4. Calls Groq Llama LLM to generate grounded response.
    5. Returns grounded answer + source citations.
    6. Writes an audit log entry.
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="User question cannot be empty.")

    user = UserContext(
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        role=request.role
    )

    try:
        # 1. Retrieve ONLY authorized chunks for the user
        authorized_chunks = permission_aware_retriever.retrieve_authorized_chunks(
            query=request.question,
            user=user,
            top_k=request.top_k or 4
        )

        # 2. Generate grounded answer
        result = retrieval_service.answer_query(
            query=request.question,
            chunks=authorized_chunks
        )

        # 3. Log audit query event
        doc_ids = list(set([
            c.metadata.get("document_id", "")
            for c in authorized_chunks if c.metadata.get("document_id")
        ]))

        audit_service.log_event(
            user=user.user_id,
            tenant_id=user.tenant_id,
            role=user.role,
            action="document_query",
            document_ids=doc_ids,
            details={
                "question": request.question,
                "retrieved_count": len(authorized_chunks),
                "has_sources": len(result.get("sources", [])) > 0
            }
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )
