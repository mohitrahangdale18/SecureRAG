"""
Document Pydantic Schemas for API Requests & Responses.
"""

from typing import List
from pydantic import BaseModel, Field

class DocumentUploadResponse(BaseModel):
    document_id: str
    document_name: str
    pages_count: int
    chunks_count: int
    tenant_id: str
    department: str
    allowed_roles: List[str]

class DocumentInfo(BaseModel):
    document_id: str
    document_name: str
    department: str
    allowed_roles: List[str]
    tenant_id: str
