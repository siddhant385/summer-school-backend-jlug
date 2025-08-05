# app/services/user_workshop.py
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import HTTPException, status
from app.core.logger import setup_logger
from app.core.db import get_db, get_db_admin
from app.schemas.user_workshop import (
    RegisterUserToWorkshopSchema,
    UserWorkshopRelation,
    WorkshopUser,
    FetchWorkshopUsersResponse,
    UserWorkshop,
    FetchUsersWorkshopsResponse,
    UpdateReminderStatusSchema
)

log = setup_logger(__name__)


class UserWorkshopService:
    """Service for managing user-workshop relationships"""

    @staticmethod
    def register_user_to_workshop(registration_data: RegisterUserToWorkshopSchema) -> UserWorkshopRelation:
        """Register a user to a workshop"""
        try:
            log.debug(f"Registering user {registration_data.user_id} to workshop {registration_data.workshop_id}")
            
            # Check if already registered
            existing = get_db().table("user_workshop") \
                .select("*") \
                .eq("user_id", str(registration_data.user_id)) \
                .eq("workshop_id", str(registration_data.workshop_id)) \
                .execute()
            
            if existing.data:
                log.warning(f"User {registration_data.user_id} already registered for workshop {registration_data.workshop_id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User already registered for this workshop"
                )
            
            # Register user
            insert_data = {
                "user_id": str(registration_data.user_id),
                "workshop_id": str(registration_data.workshop_id),
                "reminder_1day_sent": False,
                "reminder_15min_sent": False
            }
            
            response = get_db().table("user_workshop").insert(insert_data).execute()
            
            if not response.data:
                log.error("Failed to register user - no data returned")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Registration failed"
                )
            
            registered_data = response.data[0]
            log.info(f"User {registration_data.user_id} successfully registered to workshop {registration_data.workshop_id}")
            
            return UserWorkshopRelation(
                user_id=UUID(registered_data["user_id"]),
                workshop_id=UUID(registered_data["workshop_id"]),
                created_at=datetime.fromisoformat(registered_data["created_at"].replace('Z', '+00:00')),
                reminder_1day_sent=registered_data.get("reminder_1day_sent"),
                reminder_15min_sent=registered_data.get("reminder_15min_sent")
            )
            
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except Exception as e:
            log.exception(f"Unexpected error registering user to workshop: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed due to internal error"
            )

    @staticmethod
    def get_workshop_users(workshop_id: UUID) -> FetchWorkshopUsersResponse:
        """Get all users registered for a specific workshop"""
        try:
            log.debug(f"Fetching users for workshop: {workshop_id}")
            
            response = get_db().table("user_workshop") \
                .select("""
                    user_id,
                    created_at,
                    reminder_1day_sent,
                    reminder_15min_sent,
                    user:users(id, name, email, profile_pic_url, points, role)
                """) \
                .eq("workshop_id", str(workshop_id)) \
                .execute()
            
            if not response.data:
                log.info(f"No users found for workshop: {workshop_id}")
                return FetchWorkshopUsersResponse(
                    workshop_id=workshop_id,
                    total_participants=0,
                    users=[]
                )
            
            users = []
            for item in response.data:
                user_data = item.get("user", {})
                if user_data:
                    users.append(WorkshopUser(
                        user_id=UUID(item["user_id"]),
                        name=user_data.get("name"),
                        email=user_data["email"],
                        profile_pic_url=user_data.get("profile_pic_url"),
                        points=user_data.get("points"),
                        role=user_data.get("role"),
                        reminder_1day_sent=item.get("reminder_1day_sent"),
                        reminder_15min_sent=item.get("reminder_15min_sent"),
                        created_at=datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
                    ))
            
            log.info(f"Found {len(users)} users for workshop {workshop_id}")
            
            return FetchWorkshopUsersResponse(
                workshop_id=workshop_id,
                total_participants=len(users),
                users=users
            )
            
        except Exception as e:
            log.exception(f"Error fetching workshop users for {workshop_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch workshop users"
            )

    @staticmethod
    def get_user_workshops(user_id: UUID) -> FetchUsersWorkshopsResponse:
        """Get all workshops a user is registered for"""
        try:
            log.debug(f"Fetching workshops for user: {user_id}")
            
            response = get_db().table("user_workshop") \
                .select("""
                    workshop_id,
                    created_at,
                    reminder_1day_sent,
                    reminder_15min_sent,
                    workshop:workshops(id, title, description, technologies, conducted_by, scheduled_at)
                """) \
                .eq("user_id", str(user_id)) \
                .execute()
            
            if not response.data:
                log.info(f"No workshops found for user: {user_id}")
                return FetchUsersWorkshopsResponse(
                    user_id=user_id,
                    total_workshops=0,
                    workshops=[]
                )
            
            workshops = []
            for item in response.data:
                workshop_data = item.get("workshop", {})
                if workshop_data:
                    workshops.append(UserWorkshop(
                        workshop_id=UUID(item["workshop_id"]),
                        title=workshop_data.get("title"),
                        description=workshop_data.get("description"),
                        technologies=workshop_data.get("technologies"),
                        conducted_by=workshop_data.get("conducted_by"),
                        scheduled_at=datetime.fromisoformat(workshop_data["scheduled_at"]) if workshop_data.get("scheduled_at") else None,
                        reminder_1day_sent=item.get("reminder_1day_sent"),
                        reminder_15min_sent=item.get("reminder_15min_sent"),
                        registration_date=datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
                    ))
            
            log.info(f"Found {len(workshops)} workshops for user {user_id}")
            
            return FetchUsersWorkshopsResponse(
                user_id=user_id,
                total_workshops=len(workshops),
                workshops=workshops
            )
            
        except Exception as e:
            log.exception(f"Error fetching user workshops for {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user workshops"
            )

    @staticmethod
    def update_reminder_status(reminder_data: UpdateReminderStatusSchema) -> UserWorkshopRelation:
        """Update reminder status for a user-workshop relationship"""
        try:
            log.debug(f"Updating reminder status for user {reminder_data.user_id}, workshop {reminder_data.workshop_id}")
            
            update_data = {}
            if reminder_data.reminder_1day_sent is not None:
                update_data["reminder_1day_sent"] = reminder_data.reminder_1day_sent
            if reminder_data.reminder_15min_sent is not None:
                update_data["reminder_15min_sent"] = reminder_data.reminder_15min_sent
            
            if not update_data:
                log.warning("No reminder status provided for update")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one reminder status must be provided"
                )
            
            response = get_db_admin().table("user_workshop") \
                .update(update_data) \
                .eq("user_id", str(reminder_data.user_id)) \
                .eq("workshop_id", str(reminder_data.workshop_id)) \
                .execute()
            
            if not response.data:
                log.error(f"Failed to update reminder status - user/workshop not found")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User-workshop relationship not found"
                )
            
            updated_data = response.data[0]
            log.info(f"Reminder status updated for user {reminder_data.user_id}, workshop {reminder_data.workshop_id}")
            
            return UserWorkshopRelation(
                user_id=UUID(updated_data["user_id"]),
                workshop_id=UUID(updated_data["workshop_id"]),
                created_at=datetime.fromisoformat(updated_data["created_at"].replace('Z', '+00:00')),
                reminder_1day_sent=updated_data.get("reminder_1day_sent"),
                reminder_15min_sent=updated_data.get("reminder_15min_sent")
            )
            
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except Exception as e:
            log.exception(f"Unexpected error updating reminder status")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update reminder status"
            )

    @staticmethod
    def unregister_user_from_workshop(user_id: UUID, workshop_id: UUID) -> bool:
        """Remove user registration from workshop"""
        try:
            log.debug(f"Unregistering user {user_id} from workshop {workshop_id}")
            
            response = get_db_admin().table("user_workshop") \
                .delete() \
                .eq("user_id", str(user_id)) \
                .eq("workshop_id", str(workshop_id)) \
                .execute()
            
            if not response.data:
                log.warning(f"No registration found to delete for user {user_id}, workshop {workshop_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User registration not found for this workshop"
                )
            
            log.info(f"User {user_id} successfully unregistered from workshop {workshop_id}")
            return True
            
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except Exception as e:
            log.exception(f"Error unregistering user from workshop")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unregistration failed"
            )

    @staticmethod
    def get_users_needing_reminders(workshop_id: UUID, reminder_type: str) -> List[WorkshopUser]:
        """Get users who need reminders for a specific workshop"""
        try:
            log.debug(f"Fetching users needing {reminder_type} reminders for workshop: {workshop_id}")
            
            if reminder_type not in ["1day", "15min"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reminder type. Must be '1day' or '15min'"
                )
            
            field_name = f"reminder_{reminder_type}_sent"
            
            response = get_db().table("user_workshop") \
                .select(f"""
                    user_id,
                    created_at,
                    reminder_1day_sent,
                    reminder_15min_sent,
                    user:users(id, name, email, profile_pic_url, points, role)
                """) \
                .eq("workshop_id", str(workshop_id)) \
                .eq(field_name, False) \
                .execute()
            
            users = []
            for item in response.data:
                user_data = item.get("user", {})
                if user_data:
                    users.append(WorkshopUser(
                        user_id=UUID(item["user_id"]),
                        name=user_data.get("name"),
                        email=user_data["email"],
                        profile_pic_url=user_data.get("profile_pic_url"),
                        points=user_data.get("points"),
                        role=user_data.get("role"),
                        reminder_1day_sent=item.get("reminder_1day_sent"),
                        reminder_15min_sent=item.get("reminder_15min_sent"),
                        created_at=datetime.fromisoformat(item["created_at"].replace('Z', '+00:00'))
                    ))
            
            log.info(f"Found {len(users)} users needing {reminder_type} reminders for workshop {workshop_id}")
            return users
            
        except HTTPException:
            # Re-raise HTTPExceptions as-is
            raise
        except Exception as e:
            log.exception(f"Error fetching users needing reminders")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch users needing reminders"
            )
