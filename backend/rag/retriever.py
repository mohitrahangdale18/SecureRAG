"""
Permission-Aware Vector Retriever Module.

Why it is needed:
Combines vector similarity search with security metadata filtering.
Prevents cross-tenant data leaks and unauthorized role access BEFORE chunks reach the LLM prompt.

Interview Concept:
Why over-sample during similarity search?
We query the vector store for `k * 3` candidates so that even after filtering out unauthorized chunks
belonging to other tenants or restricted roles, we still have up to `k` authorized relevant chunks for generation.
"""

import logging
from typing import List
from langchain_core.documents import Document
from backend.vectorstore.faiss_store import faiss_store
from backend.services.permission_service import permission_service
from backend.schemas.user import UserContext
from backend.config import settings

logger = logging.getLogger(__name__)

class PermissionAwareRetriever:
    def retrieve_authorized_chunks(
        self,
        query: str,
        user: UserContext,
        top_k: int = settings.DEFAULT_TOP_K
    ) -> List[Document]:
        """
        Retrieves candidate chunks from vector store and enforces strict permission filtering.
        Returns only chunks authorized for the user's tenant_id and role.
        """
        # Fetch candidate chunks (over-sample to compensate for permission filtering)
        fetch_k = max(top_k * 3, 12)
        raw_candidates = faiss_store.similarity_search(query, k=fetch_k)

        logger.info(f"Retrieved {len(raw_candidates)} candidate chunks from vector store for query: '{query}'")

        # Apply security & tenant filter
        authorized_chunks = permission_service.filter_chunks(raw_candidates, user)

        logger.info(
            f"User '{user.user_id}' (Tenant: '{user.tenant_id}', Role: '{user.role}') "
            f"authorized for {len(authorized_chunks)} / {len(raw_candidates)} chunks."
        )

        # Truncate to top_k authorized chunks
        return authorized_chunks[:top_k]

# Global singleton retriever instance
permission_aware_retriever = PermissionAwareRetriever()
