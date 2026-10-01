"""
Permission Validation Service Module.

Why it is needed:
SecureRAG's most critical feature is permission-aware retrieval.
This service evaluates security metadata on retrieved document chunks against the requesting user's identity context.

Interview Concept:
1. Multi-Tenant Isolation: Data belonging to tenant_id = 'company_a' must NEVER be accessible to 'company_b'.
2. Role-Based Access Control (RBAC): Even within tenant 'company_a', an ENGINEERING user must not view HR or FINANCE restricted chunks.
3. Defense in Depth: Filtering happens inside the retrieval service before passing text to the LLM. Unauthorized content never enters the LLM prompt.
"""

import logging
from typing import List, Dict, Any
from langchain_core.documents import Document
from backend.schemas.user import User, UserContext

logger = logging.getLogger(__name__)

class PermissionService:
    def is_chunk_authorized(self, chunk: Document, user: UserContext) -> bool:
        """
        Evaluates authorization rules for a single document chunk against user identity context.
        """
        metadata = chunk.metadata or {}
        chunk_tenant = metadata.get("tenant_id", "")
        allowed_roles = metadata.get("allowed_roles", [])

        # Ensure allowed_roles is a list/collection
        if isinstance(allowed_roles, str):
            allowed_roles = [allowed_roles]

        # Rule 1: Strict Tenant Isolation
        if chunk_tenant != user.tenant_id:
            logger.warning(
                f"[PERM DENIED] Tenant mismatch. User tenant '{user.tenant_id}' tried to access chunk from tenant '{chunk_tenant}'"
            )
            return False

        # Rule 2: Role Authorization
        user_role = user.role.upper()
        allowed_roles_upper = [r.upper() for r in allowed_roles]

        # ADMIN role has full access to all documents within their tenant
        if user_role == "ADMIN":
            return True

        if user_role in allowed_roles_upper:
            return True

        logger.warning(
            f"[PERM DENIED] Role mismatch. User role '{user.role}' is not in allowed roles {allowed_roles} for doc '{metadata.get('document_name')}'"
        )
        return False

    def filter_chunks(self, chunks: List[Document], user: UserContext) -> List[Document]:
        """
        Filters a list of document chunks, returning ONLY authorized chunks for the given user context.
        """
        authorized_chunks = []
        for chunk in chunks:
            if self.is_chunk_authorized(chunk, user):
                authorized_chunks.append(chunk)
            else:
                logger.info(
                    f"Filtered out unauthorized chunk: doc={chunk.metadata.get('document_name')}, "
                    f"tenant={chunk.metadata.get('tenant_id')}, allowed={chunk.metadata.get('allowed_roles')}"
                )

        return authorized_chunks

permission_service = PermissionService()
