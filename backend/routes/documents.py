"""
Document Management Routes.
"""

import os
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from backend.config import settings
from backend.schemas.user import UserContext, DEMO_USERS
from backend.schemas.document import DocumentUploadResponse, DocumentInfo
from backend.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form("rahul"),
    tenant_id: str = Form("company_a"),
    role: str = Form("HR"),
    department: str = Form("HR"),
    allowed_roles: str = Form("HR,ADMIN")
):
    """
    Uploads a PDF file, parses page text, chunks content, attaches permission metadata,
    and indexes vectors into persistent FAISS storage.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    user = UserContext(user_id=user_id, tenant_id=tenant_id, role=role)
    roles_list = [r.strip().upper() for r in allowed_roles.split(",") if r.strip()]
    if not roles_list:
        roles_list = ["ADMIN"]

    # Save uploaded file temporarily to data/uploads
    temp_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process and index PDF
        result = document_service.process_and_index_pdf(
            file_path=temp_path,
            filename=file.filename,
            user=user,
            department=department.upper(),
            allowed_roles=roles_list
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
    finally:
        # Clean up temporary upload file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

@router.get("", response_model=List[DocumentInfo])
def list_documents(
    tenant_id: str = Query("company_a"),
    user_id: str = Query("rahul"),
    role: str = Query("HR")
):
    """
    Returns list of indexed documents accessible to the requesting user's tenant and role.
    """
    user = UserContext(user_id=user_id, tenant_id=tenant_id, role=role)
    return document_service.list_accessible_documents(user)
