"""
FAISS Vector Store Manager.

Why it is needed:
FAISS (Facebook AI Similarity Search) provides high-performance vector indexing and similarity search.
It stores vector representations of text chunks alongside their metadata dictionaries.

Interview Concept:
1. Persistent Indexing: `save_local` and `load_local` allow vector indices to persist on disk so embeddings don't need to be recomputed when the server restarts.
2. Metadata Association: FAISS maintains an internal `docstore` mapping each vector ID to its original text chunk and metadata (tenant_id, allowed_roles, source, page).
"""

import os
import logging
from typing import List, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from backend.config import settings
from backend.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    def __init__(self, index_dir: str = settings.VECTOR_STORE_DIR):
        self.index_dir = index_dir
        self.vector_store: Optional[FAISS] = None
        self.reload_index()

    def reload_index(self) -> None:
        """Loads FAISS index from disk if present."""
        embeddings = embedding_service.get_embeddings()
        index_file = os.path.join(self.index_dir, "index.faiss")
        if os.path.exists(index_file):
            try:
                self.vector_store = FAISS.load_local(
                    folder_path=self.index_dir,
                    embeddings=embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"FAISS index loaded successfully from {self.index_dir}")
            except Exception as e:
                logger.warning(f"Could not load existing FAISS index: {e}. Index will be created on first document upload.")
                self.vector_store = None
        else:
            self.vector_store = None

    def add_documents(self, documents: List[Document]) -> None:
        """
        Adds document chunks to the FAISS index and persists to disk.
        """
        if not documents:
            return

        embeddings = embedding_service.get_embeddings()
        if self.vector_store is None:
            self.vector_store = FAISS.from_documents(documents, embeddings)
        else:
            self.vector_store.add_documents(documents)

        # Persist updated vector index to disk
        self.vector_store.save_local(self.index_dir)
        logger.info(f"Added {len(documents)} document chunks to FAISS index at {self.index_dir}")

    def similarity_search(self, query: str, k: int = 10) -> List[Document]:
        """
        Performs vector similarity search returning top-k matching chunks.
        Note: Metadata filtering for multi-tenancy & permissions is applied at retrieval time.
        """
        if self.vector_store is None:
            return []
        return self.vector_store.similarity_search(query, k=k)

    def get_all_documents(self) -> List[Document]:
        """
        Returns all indexed document chunks stored in FAISS docstore.
        """
        if self.vector_store is None or not hasattr(self.vector_store, "docstore"):
            return []
        return list(self.vector_store.docstore._dict.values())

# Global singleton vector store instance
faiss_store = FAISSVectorStore()
