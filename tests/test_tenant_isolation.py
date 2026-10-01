"""
Test Strict Multi-Tenant Data Isolation.

Verifies that users belonging to Tenant A (company_a) can NEVER retrieve data from Tenant B (company_b),
even if they hold identical role names (e.g. HR or ADMIN).
"""

from langchain_core.documents import Document
from backend.services.permission_service import permission_service
from backend.schemas.user import UserContext

def test_tenant_isolation_denies_cross_tenant_access():
    # Document belonging to Company B
    company_b_doc = Document(
        page_content="Company B Confidential Q3 Revenue Report.",
        metadata={
            "tenant_id": "company_b",
            "document_name": "company_b_q3.pdf",
            "allowed_roles": ["HR", "ADMIN", "FINANCE"]
        }
    )

    # Rahul belongs to Company A (HR)
    rahul_a = UserContext(user_id="rahul", tenant_id="company_a", role="HR")
    assert permission_service.is_chunk_authorized(company_b_doc, rahul_a) is False

    # Admin A belongs to Company A (ADMIN)
    admin_a = UserContext(user_id="admin_a", tenant_id="company_a", role="ADMIN")
    assert permission_service.is_chunk_authorized(company_b_doc, admin_a) is False

def test_tenant_isolation_allows_same_tenant_access():
    # Document belonging to Company B
    company_b_doc = Document(
        page_content="Company B Confidential HR Policy.",
        metadata={
            "tenant_id": "company_b",
            "document_name": "company_b_policy.pdf",
            "allowed_roles": ["HR"]
        }
    )

    # Neha belongs to Company B (HR) -> ALLOWED
    neha_b = UserContext(user_id="neha", tenant_id="company_b", role="HR")
    assert permission_service.is_chunk_authorized(company_b_doc, neha_b) is True
