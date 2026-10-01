"""
Demo User Management Routes.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from backend.schemas.user import User, DEMO_USERS

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=List[User])
def get_all_users():
    """Returns the list of demo users available in the system."""
    return DEMO_USERS

@router.get("/{user_id}", response_model=User)
def get_user_by_id(user_id: str):
    """Retrieves identity context for a specific demo user."""
    for u in DEMO_USERS:
        if u.user_id.lower() == user_id.lower():
            return u
    raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")
