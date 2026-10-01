"""
Embedding Service Module.

Why it is needed:
In a RAG system, text chunks and user queries must be transformed into dense vector representations (embeddings).
These vectors capture semantic meaning, allowing vector databases like FAISS to perform fast similarity searches.

Model Used:
BAAI/bge-small-en-v1.5 (Hugging Face via SentenceTransformers).
Produces 384-dimensional normalized embeddings fine-tuned for retrieval tasks.
"""

from typing import Any
from backend.config import settings

class EmbeddingService:
    def __init__(self):
        self._embeddings = None

    def get_embeddings(self) -> Any:
        """
        Lazy initializer for HuggingFace embeddings model.
        Returns a LangChain-compatible embedding object.
        """
        if self._embeddings is None:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                self._embeddings = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL_NAME,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
            except ImportError:
                from langchain_community.embeddings import HuggingFaceEmbeddings
                self._embeddings = HuggingFaceEmbeddings(
                    model_name=settings.EMBEDDING_MODEL_NAME,
                    model_kwargs={'device': 'cpu'},
                    encode_kwargs={'normalize_embeddings': True}
                )
        return self._embeddings

# Global singleton instance to avoid reloading heavy model multiple times
embedding_service = EmbeddingService()
