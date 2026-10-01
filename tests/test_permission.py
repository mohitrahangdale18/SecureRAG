"""
Test Permission Service & Role-Based Access Control (RBAC).
"""

from langchain_core.documents import Document
from backend.services.permission_service import permission_service
from backend.schemas.user import UserContext

def test_role_based_access_control():
    # Document restricted to HR and ADMIN roles in Company A
    hr_doc = Document(
        page_content="Salary reviews occur every December.",
        metadata={
            "tenant_id": "company_a",
            "document_name": "compensation_guide.pdf",
            "allowed_roles": ["HR", "ADMIN"]
        }
    )

    # User 1: Rahul (Company A, HR) -> ALLOWED
    rahul = UserContext(user_id="rahul", tenant_id="company_a", role="HR")
    assert permission_service.is_chunk_authorized(hr_doc, rahul) is True

    # User 2: Amit (Company A, ENGINEERING) -> DENIED
    amit = UserContext(user_id="amit", tenant_id="company_a", role="ENGINEERING")
    assert permission_service.is_chunk_authorized(hr_doc, amit) is False

    # User 3: Admin A (Company A, ADMIN) -> ALLOWED
    admin_a = UserContext(user_id="admin_a", tenant_id="company_a", role="ADMIN")
    assert permission_service.is_chunk_authorized(hr_doc, admin_a) is True

def test_filter_chunks():
    chunks = [
        Document(
            page_content="HR doc content",
            metadata={"tenant_id": "company_a", "allowed_roles": ["HR"]}
        ),
        Document(
            page_content="Engineering doc content",
            metadata={"tenant_id": "company_a", "allowed_roles": ["ENGINEERING"]}
        )
    ]

    rahul = UserContext(user_id="rahul", tenant_id="company_a", role="HR")
    filtered = permission_service.filter_chunks(chunks, rahul)

    assert len(filtered) == 1
    assert filtered[0].page_content == "HR doc content"
