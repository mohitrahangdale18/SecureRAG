import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
    VECTOR_STORE_DIR: str = str(BASE_DIR / os.getenv("VECTOR_STORE_DIR", "data/faiss_index"))
    UPLOAD_DIR: str = str(BASE_DIR / "data" / "uploads")
    AUDIT_LOG_FILE: str = str(BASE_DIR / "data" / "audit_logs.jsonl")
    DEFAULT_TOP_K: int = int(os.getenv("DEFAULT_TOP_K", "4"))
    
    # Sensible RAG default parameters
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100

settings = Settings()

# Ensure data directories exist
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(settings.AUDIT_LOG_FILE), exist_ok=True)
