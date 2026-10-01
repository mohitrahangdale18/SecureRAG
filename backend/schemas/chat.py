"""
Chat Request & Response Pydantic Schemas.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    user_id: str = Field(..., json_schema_extra={"example": "rahul"})
    tenant_id: str = Field(..., json_schema_extra={"example": "company_a"})
    role: str = Field(..., json_schema_extra={"example": "HR"})
    question: str = Field(..., json_schema_extra={"example": "What is the annual leave policy?"})
    top_k: Optional[int] = Field(4, ge=1, le=20)

class SourceCitation(BaseModel):
    document_name: str
    page: Any
    document_id: Optional[str] = ""
    department: Optional[str] = ""

class ChunkPreview(BaseModel):
    content: str
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    query: str
    answer: str
    sources: List[SourceCitation]
    retrieved_chunks_count: int
    chunks: Optional[List[ChunkPreview]] = []
