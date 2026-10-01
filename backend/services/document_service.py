"""
Document Service Module.

Why it is needed:
Orchestrates PDF file ingestion, chunking, FAISS vector indexing, metadata tagging, and audit trail generation.
Also provides filtered listing of indexed documents accessible to the current user.
"""

import os
import logging
from typing import List, Dict, Any
from backend.config import settings
from backend.rag.ingestion import load_pdf_document
from backend.rag.chunking import chunk_documents
from backend.vectorstore.faiss_store import faiss_store
from backend.services.audit_service import audit_service
from backend.schemas.user import UserContext

logger = logging.getLogger(__name__)

class DocumentService:
    def process_and_index_pdf(
        self,
        file_path: str,
        filename: str,
        user: UserContext,
        department: str,
        allowed_roles: List[str]
    ) -> Dict[str, Any]:
        """
        Ingests a PDF file, splits into chunks with permission metadata, updates FAISS store, and writes an audit event.
        """
        clean_name = os.path.basename(filename)
        doc_id = f"doc_{os.path.splitext(clean_name)[0]}"

        doc_metadata = {
            "tenant_id": user.tenant_id,
            "document_id": doc_id,
            "document_name": clean_name,
            "department": department,
            "allowed_roles": allowed_roles
        }

        # 1. Parse PDF pages into Documents with metadata
        documents = load_pdf_document(file_path, doc_metadata)

        # 2. Chunk text while retaining metadata
        chunks = chunk_documents(documents)

        # 3. Add vector embeddings to persistent FAISS index
        faiss_store.add_documents(chunks)

        # 4. Audit log event
        audit_service.log_event(
            user=user.user_id,
            tenant_id=user.tenant_id,
            role=user.role,
            action="document_upload_index",
            document_ids=[doc_id],
            details={
                "document_name": clean_name,
                "pages_count": len(documents),
                "chunks_count": len(chunks),
                "department": department,
                "allowed_roles": allowed_roles
            }
        )

        return {
            "document_id": doc_id,
            "document_name": clean_name,
            "pages_count": len(documents),
            "chunks_count": len(chunks),
            "tenant_id": user.tenant_id,
            "department": department,
            "allowed_roles": allowed_roles
        }

    def list_accessible_documents(self, user: UserContext) -> List[Dict[str, Any]]:
        """
        Returns unique documents indexed in vector store that the user is authorized to view.
        """
        all_chunks = faiss_store.get_all_documents()
        seen_docs: Dict[str, Dict[str, Any]] = {}

        for chunk in all_chunks:
            meta = chunk.metadata or {}
            tenant = meta.get("tenant_id", "")
            roles = meta.get("allowed_roles", [])
            doc_id = meta.get("document_id", "unknown")

            # Check tenant isolation
            if tenant == user.tenant_id:
                user_role = user.role.upper()
                allowed_upper = [r.upper() for r in roles] if isinstance(roles, list) else [roles.upper()]

                # Check role access
                if user_role == "ADMIN" or user_role in allowed_upper:
                    if doc_id not in seen_docs:
                        seen_docs[doc_id] = {
                            "document_id": doc_id,
                            "document_name": meta.get("document_name", "Unknown"),
                            "department": meta.get("department", "GENERAL"),
                            "allowed_roles": roles,
                            "tenant_id": tenant
                        }

        return list(seen_docs.values())

document_service = DocumentService()
