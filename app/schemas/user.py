# In app/schemas/user.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

# Defines the roles a user can have
class UserRole(str, Enum):
    guest = "guest"
    user = "user"
    admin = "admin"

# Common base fields for a user
class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    profile_pic_url: Optional[str] = None

# Internal model for creating a user in the database
# This will be used by your backend services, not by a direct API call from the frontend
class UserCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    auth_id: Optional[UUID] = None      # From Supabase JWT
    profile_pic_url: Optional[str] = None
    points: Optional[int] = 0
    role: UserRole = UserRole.guest     # Default role is guest

# Schema for updating a user's profile information
class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_pic_url: Optional[str] = None

# Schema for upgrading user role (guest to user)
class UserRoleUpgrade(BaseModel):
    auth_id: UUID                       # From Supabase JWT token
    role: UserRole = UserRole.user      # Target role (usually guest to user)

# The main user model that will be returned by the API
class User(UserBase):
    id: UUID                            # Your internal database's Primary Key
    auth_id: Optional[UUID] = None      # Supabase auth user ID
    created_at: datetime
    points: Optional[int] = 0
    role: UserRole

    class Config:
        # Allows Pydantic to read data from database objects
        from_attributes = True