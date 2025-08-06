# app/schemas/user.py
"""
User-related Pydantic schemas based on database structure.
Database schema reference:
- id: UUID (primary key, auto-generated)
- created_at: timestamp with time zone
- auth_id: UUID (Supabase auth ID, nullable)
- email: text (unique, required)
- profile_pic_url: text (nullable)
- points: integer (nullable)
- role: text (default 'guest')
- profile_complete: boolean (default false)
- name: text (nullable)

Future extensible fields that may be added:
- updated_at, is_deleted, bio, phone, college, year, linkedin, github, etc.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles matching database enum values."""
    guest = "guest"
    user = "user" 
    admin = "admin"


class UserBase(BaseModel):
    """Base user fields for common operations."""
    email: EmailStr
    name: Optional[str] = None
    profile_pic_url: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for creating new users in database."""
    email: EmailStr
    name: Optional[str] = None
    auth_id: Optional[UUID] = None
    profile_pic_url: Optional[str] = None
    points: Optional[int] = Field(default=0, ge=0)
    role: UserRole = UserRole.guest


class UserUpdate(BaseModel):
    """Schema for updating user profile information."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    profile_pic_url: Optional[str] = Field(None, min_length=1)


class UserRoleUpgrade(BaseModel):
    """Schema for upgrading user role (guest -> user)."""
    auth_id: UUID
    role: UserRole = UserRole.user


class User(BaseModel):
    """Complete user model matching database structure."""
    id: UUID
    created_at: datetime
    auth_id: Optional[UUID] = None
    email: EmailStr
    profile_pic_url: Optional[str] = None
    points: Optional[int] = 0
    role: UserRole
    profile_complete: bool = False
    name: Optional[str] = None

    class Config:
        from_attributes = True


# Response schemas for API operations
class ProfileCompletionStatus(BaseModel):
    """Profile completion status response."""
    is_complete: bool
    completion_percentage: int
    missing_fields: List[Dict[str, str]]
    completed_fields: List[str]
    newly_completed: bool = False
    points_awarded: int = 0


class UserOperationResponse(BaseModel):
    """Standard user operation response with profile status."""
    user: User
    profile_status: Optional[ProfileCompletionStatus] = None


class UserListResponse(BaseModel):
    """Response for user search/list operations."""
    users: List[User]
    total_count: int
    search_query: Optional[str] = None


class UserPointsResponse(BaseModel):
    """Response for points-related operations."""
    user: User
    points_added: int
    new_total: int