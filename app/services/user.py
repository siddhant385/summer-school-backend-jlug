# app/services/user.py

from uuid import UUID
from fastapi import HTTPException, status
from app.schemas.user import (
    UserUpdate, User, ProfileCompletionStatus, UserOperationResponse, 
    UserPointsResponse, UserListResponse
)
from app.schemas.response import ResponseModel
from app.core.logger import setup_logger
from app.core.db import get_db, get_db_admin
from typing import Dict, Any, List

log = setup_logger(__name__)

class UserService:

    @staticmethod
    def update_user(user_id: UUID, data: UserUpdate) -> ResponseModel[UserOperationResponse]:
        """
        Update name or profile picture for a user.
        Automatically checks profile completion and awards points if completed.
        
        Returns ResponseModel with user and profile status.
        """
        db = get_db_admin()
        try:
            log.debug(f"Updating user: {user_id}")
            
            # Use model_dump instead of deprecated dict()
            update_data = data.model_dump(exclude_unset=True)
            if not update_data:
                log.warning(f"No fields provided for user update: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="No fields to update"
                )

            response = db.table("users").update(update_data).eq("id", str(user_id)).execute()
            
            if not response.data:
                log.warning(f"User not found for update: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User not found"
                )

            # Get updated user data
            user_response = db.table("users").select("*").eq("id", str(user_id)).single().execute()
            updated_user = User(**user_response.data)
            log.info(f"User {user_id} updated with {list(update_data.keys())}")
            
            # 🎯 Automatic profile completion check after update
            profile_check_response = UserService.is_profile_complete(user_id)
            profile_status = profile_check_response.data
            
            # Log profile completion status
            if profile_status.newly_completed:
                log.info(f"🎉 Profile completed for user {user_id}! Awarded {profile_status.points_awarded} points.")
            elif profile_status.is_complete:
                log.debug(f"Profile already complete for user {user_id}")
            else:
                log.debug(f"Profile {profile_status.completion_percentage}% complete for user {user_id}")
            
            user_response_data = UserOperationResponse(
                user=updated_user,
                profile_status=profile_status
            )
            
            return ResponseModel[UserOperationResponse](
                success=True,
                message=f"User profile updated successfully. Profile {profile_status.completion_percentage}% complete.",
                data=user_response_data
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error updating user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to update user"
            )

    @staticmethod
    def increment_user_points(user_id: UUID, amount: int) -> ResponseModel[UserPointsResponse]:
        """Increment user's points and return updated user with points info."""
        db = get_db_admin()
        try:
            log.debug(f"Incrementing points for user {user_id}: +{amount}")
            
            # Input validation
            if amount <= 0:
                log.warning(f"Invalid points amount: {amount}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Points amount must be positive"
                )

            # Get current user data first
            current_user_response = db.table("users").select("points").eq("id", str(user_id)).single().execute()
            if not current_user_response.data:
                log.warning(f"User not found for points increment: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User not found"
                )
            
            current_points = current_user_response.data.get("points", 0) or 0
            new_total = current_points + amount

            # Increment points manually (since DB function doesn't exist)
            response = db.table("users").update({
                "points": new_total
            }).eq("id", str(user_id)).execute()

            if not response.data:
                log.error(f"Failed to increment points for user: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail="Failed to increment points"
                )

            # Get updated user data
            updated_user_response = db.table("users").select("*").eq("id", str(user_id)).single().execute()
            updated_user = User(**updated_user_response.data)
            
            points_response_data = UserPointsResponse(
                user=updated_user,
                points_added=amount,
                new_total=new_total
            )

            log.info(f"Points incremented for user {user_id}: +{amount} (total: {new_total})")
            
            return ResponseModel[UserPointsResponse](
                success=True,
                message=f"Added {amount} points. New total: {new_total}",
                data=points_response_data
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error incrementing points for {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to increment user points"
            )

    @staticmethod
    def is_profile_complete(user_id: UUID) -> ResponseModel[ProfileCompletionStatus]:
        """
        Dynamic profile completion checker - future-proof for new fields.
        
        Returns ResponseModel with profile completion details.
        """
        db = get_db_admin()
        try:
            log.debug(f"Checking dynamic profile completion for user: {user_id}")
            
            # Get all user data to check completeness
            response = db.table("users").select("*").eq("id", str(user_id)).single().execute()

            if not response.data:
                log.warning(f"User not found for profile check: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User not found"
                )

            user_data = response.data
            current_profile_complete = user_data.get("profile_complete", False)
            
            # Define required fields for complete profile (future-proof)
            required_fields = {
                "name": "Full name",
                "profile_pic_url": "Profile picture",
                # Future fields can be added here:
                # "bio": "Bio/Description", 
                # "year": "Year of study",
                # "college": "College name",
                # "phone": "Phone number",
                # "linkedin": "LinkedIn profile",
                # "github": "GitHub profile"
            }
            
            # Check which fields are missing
            missing_fields = []
            filled_fields = []
            
            for field, description in required_fields.items():
                value = user_data.get(field)
                if not value or (isinstance(value, str) and not value.strip()):
                    missing_fields.append({"field": field, "description": description})
                else:
                    filled_fields.append(field)
            
            # Calculate completion percentage
            total_fields = len(required_fields)
            completed_fields = len(filled_fields)
            completion_percentage = int((completed_fields / total_fields) * 100) if total_fields > 0 else 0
            
            # Check if profile is now complete
            is_complete = len(missing_fields) == 0
            newly_completed = is_complete and not current_profile_complete
            
            # If profile just became complete, mark it and reward points
            if newly_completed:
                # Get current points
                current_points = user_data.get("points", 0) or 0
                new_points = current_points + 10
                
                # Update profile_complete status and add points
                db.table("users").update({
                    "profile_complete": True,
                    "points": new_points
                }).eq("id", str(user_id)).execute()
                
                log.info(f"🎉 User {user_id} profile completed! Awarded 10 points.")
            
            profile_status = ProfileCompletionStatus(
                is_complete=is_complete,
                missing_fields=missing_fields,
                completed_fields=filled_fields,
                completion_percentage=completion_percentage,
                newly_completed=newly_completed,
                points_awarded=10 if newly_completed else 0
            )
            
            log.debug(f"Profile check result for {user_id}: {completion_percentage}% complete")
            
            message = "Profile already complete" if is_complete else f"Profile {completion_percentage}% complete"
            if newly_completed:
                message = "🎉 Profile completed! 10 points awarded!"
            
            return ResponseModel[ProfileCompletionStatus](
                success=True,
                message=message,
                data=profile_status
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error checking profile completion for {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to check profile completion"
            )

    @staticmethod
    def get_profile_completion_status(user_id: UUID) -> ResponseModel[ProfileCompletionStatus]:
        """
        Get profile completion status without triggering updates.
        Useful for frontend to show completion progress.
        """
        try:
            log.debug(f"Getting profile completion status for user: {user_id}")
            return UserService.is_profile_complete(user_id)
        except Exception as e:
            log.error(f"Error getting profile status for {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get profile status"
            )

    @staticmethod
    def delete_user_by_id(user_id: UUID) -> ResponseModel[User]:
        """Soft delete user by setting profile_complete=false (admin-only)."""
        db = get_db_admin()
        try:
            log.debug(f"Soft deleting user: {user_id}")
            
            # Check if user exists first
            existing = db.table("users").select("*").eq("id", str(user_id)).single().execute()
            if not existing.data:
                log.warning(f"User not found for deletion: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User not found"
                )

            # Soft delete by marking profile as incomplete
            response = db.table("users").update({
                "profile_complete": False,
                "name": None,
                "profile_pic_url": None
            }).eq("id", str(user_id)).select("*").execute()

            if not response.data:
                log.error(f"Failed to delete user: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Delete operation failed"
                )

            deleted_user = User(**response.data[0])
            log.info(f"User soft deleted: {user_id} (email: {deleted_user.email})")
            
            return ResponseModel[User](
                success=True,
                message=f"User {deleted_user.email} successfully deactivated",
                data=deleted_user
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error deleting user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to delete user"
            )

    @staticmethod
    def search_users_by_name(name_query: str) -> ResponseModel[UserListResponse]:
        """Search users by partial name (case-insensitive)."""
        db = get_db()
        try:
            log.debug(f"Searching users by name: '{name_query}'")
            
            # Input validation
            if not name_query or len(name_query.strip()) < 2:
                log.warning(f"Invalid search query: '{name_query}'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Search query must be at least 2 characters long"
                )

            clean_query = name_query.strip()
            response = db.table("users").select("*").eq("profile_complete", True).ilike("name", f"%{clean_query}%").execute()
            
            users = [User(**u) for u in response.data or []]
            
            search_response_data = UserListResponse(
                users=users,
                total_count=len(users),
                search_query=clean_query
            )
            
            log.debug(f"Found {len(users)} users matching '{clean_query}'")
            
            message = f"Found {len(users)} users matching '{clean_query}'"
            if len(users) == 0:
                message = f"No users found matching '{clean_query}'"
            
            return ResponseModel[UserListResponse](
                success=True,
                message=message,
                data=search_response_data
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error searching users by name '{name_query}': {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to search users"
            )

    @staticmethod
    def get_all_users_paginated(offset: int, limit: int) -> ResponseModel[UserListResponse]:
        """Fetch paginated users."""
        db = get_db()
        try:
            log.debug(f"Fetching paginated users: offset={offset}, limit={limit}")
            
            # Input validation
            if offset < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Offset must be non-negative"
                )
            if limit <= 0 or limit > 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Limit must be between 1 and 100"
                )

            response = db.table("users").select("*").range(offset, offset + limit - 1).execute()
            users = [User(**u) for u in response.data or []]
            
            # Get total count
            count_response = db.table("users").select("id", count="exact").execute()
            total_count = count_response.count if count_response.count is not None else 0
            
            paginated_response_data = UserListResponse(
                users=users,
                total_count=total_count
            )
            
            log.debug(f"Retrieved {len(users)} users (offset={offset}, limit={limit})")
            
            return ResponseModel[UserListResponse](
                success=True,
                message=f"Retrieved {len(users)} users (page {offset//limit + 1})",
                data=paginated_response_data
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error fetching paginated users: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to fetch users"
            )

    @staticmethod
    def get_user_by_id(user_id: UUID) -> ResponseModel[User]:
        """Fetch user by UUID."""
        db = get_db()
        try:
            log.debug(f"Fetching user by ID: {user_id}")
            
            response = db.table("users").select("*").eq("id", str(user_id)).single().execute()

            if not response.data:
                log.warning(f"User not found: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail="User not found"
                )

            user = User(**response.data)
            log.debug(f"User retrieved: {user.email} (ID: {user_id})")
            
            return ResponseModel[User](
                success=True,
                message="User retrieved successfully",
                data=user
            )

        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error fetching user {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Failed to fetch user"
            )
