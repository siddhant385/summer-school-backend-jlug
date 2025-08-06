# app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from app.schemas.user import User, UserUpdate, UserOperationResponse, UserPointsResponse, UserListResponse, ProfileCompletionStatus
from app.schemas.response import ResponseModel
from app.services.user import UserService
from app.dependencies.auth import authenticate_and_create_user, require_admin, verify_valid_token

router = APIRouter(prefix="/users", tags=["Users"])


# 🔄 Update Current User Profile (JWT-based, more secure)
@router.put("/me", response_model=ResponseModel[UserOperationResponse])
def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(authenticate_and_create_user)
):
    """Update your own profile (name, profile_pic_url). JWT identifies the user."""
    return UserService.update_user(current_user.id, data)


# ✅ Get My Profile Completion Status (JWT-based)
@router.get("/me/profile/status", response_model=ResponseModel[ProfileCompletionStatus])
def get_my_profile_completion_status(
    current_user: User = Depends(authenticate_and_create_user)
):
    """Get your profile completion status with missing fields and percentage."""
    return UserService.get_profile_completion_status(current_user.id)


# 👤 Get My Profile (JWT-based)
@router.get("/me", response_model=ResponseModel[User])
def get_my_profile(
    current_user: User = Depends(authenticate_and_create_user)
):
    """Get your own user profile details."""
    return UserService.get_user_by_id(current_user.id)


# 🔍 Search Users (Authenticated users only) - MUST be before /{user_id}
@router.get("/search", response_model=ResponseModel[UserListResponse])
def search_users(
    name_query: str,
    current_user: User = Depends(authenticate_and_create_user)
):
    """Search users by name (minimum 2 characters required). Authenticated users only."""
    return UserService.search_users_by_name(name_query)


# 📄 Get All Users (Admin only) - MUST be before /{user_id}
@router.get("", response_model=ResponseModel[UserListResponse])
def get_all_users(
    offset: int = 0, 
    limit: int = 10,
    admin_email: str = Depends(require_admin)
):
    """Get paginated list of all users (admin only access)."""
    return UserService.get_all_users_paginated(offset, limit)


# 🎯 Increment User Points (Admin only) - Keep user_id for admin operations
@router.post("/{user_id}/points", response_model=ResponseModel[UserPointsResponse])
def increment_user_points(
    user_id: UUID,
    amount: int,
    admin_email: str = Depends(require_admin)
):
    """Increment user points (admin only). Returns user with points details."""
    return UserService.increment_user_points(user_id, amount)


# 🧹 Delete User (Admin only) - Keep user_id for admin operations
@router.delete("/{user_id}", response_model=ResponseModel[User])
def delete_user(
    user_id: UUID,
    admin_email: str = Depends(require_admin)
):
    """Soft delete user by deactivating profile (admin only)."""
    return UserService.delete_user_by_id(user_id)


# � Get User by ID (Admin only) - MUST be last among dynamic routes
@router.get("/{user_id}", response_model=ResponseModel[User])
def get_user_by_id(
    user_id: UUID,
    admin_email: str = Depends(require_admin)
):
    """Get user details by ID (admin only access)."""
    return UserService.get_user_by_id(user_id)
