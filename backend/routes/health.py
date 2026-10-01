"""
Health Check Routes.
"""

from fastapi import APIRouter
from backend.config import settings

router = APIRouter(tags=["Health"])

@router.get("/")
def root():
    return {
        "status": "online",
        "app_name": "SecureRAG - Permission-Aware Multi-Tenant Platform",
        "version": "1.0.0"
    }

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "vector_store_dir": settings.VECTOR_STORE_DIR,
        "embedding_model": settings.EMBEDDING_MODEL_NAME
    }
