"""
User and Tenant Data Schemas.

Defines Pydantic models for Demo Users, Roles, and Tenants.
"""

from typing import List
from pydantic import BaseModel, Field

class User(BaseModel):
    user_id: str
    name: str
    tenant_id: str
    role: str

class UserContext(BaseModel):
    user_id: str
    tenant_id: str
    role: str

# Pre-configured demo users matching requirements
DEMO_USERS: List[User] = [
    User(user_id="rahul", name="Rahul (HR)", tenant_id="company_a", role="HR"),
    User(user_id="amit", name="Amit (Engineering)", tenant_id="company_a", role="ENGINEERING"),
    User(user_id="admin_a", name="Admin A (System Admin)", tenant_id="company_a", role="ADMIN"),
    User(user_id="neha", name="Neha (HR)", tenant_id="company_b", role="HR"),
    User(user_id="admin_b", name="Admin B (System Admin)", tenant_id="company_b", role="ADMIN"),
]
