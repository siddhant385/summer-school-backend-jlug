# app/routers/user_workshop.py
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from typing import List

from app.core.logger import setup_logger
from app.services.user_workshop import UserWorkshopService
from app.services.assignment import AssignmentService
from app.schemas.response import ResponseModel
from app.schemas.user_workshop import (
    RegisteredUserRegistrationSchema,
    GuestRegistrationSchema,
    RegistrationResponseSchema,
    FetchWorkshopUsersResponse,
    FetchUsersWorkshopsResponse,
    UpdateReminderStatusSchema,
    UserWorkshopRelation
)
from app.schemas.user import User
from app.dependencies.user_workshop import (
    get_current_registered_user,
    get_or_create_guest_account
)
from app.dependencies.auth import require_admin

router = APIRouter(prefix="/user-workshop", tags=["Workshop Registration"])
log = setup_logger(__name__)


# 🟢 Route 1: Registered User Registration
@router.post("/register/registered-user", response_model=ResponseModel[RegistrationResponseSchema])
async def register_registered_user_to_workshop(
    registration_data: RegisteredUserRegistrationSchema,
    current_user: User = Depends(get_current_registered_user)
):
    """
    Register an authenticated user to a workshop
    - Requires valid JWT token
    - User must not be a guest
    - Prevents duplicate registrations
    - Auto-creates assignment for enrolled workshop
    """
    try:
        log.info(f"Registered user {current_user.email} attempting to register for workshop {registration_data.workshop_id}")
        
        # Check for duplicate registration by trying to get user workshops
        try:
            user_workshops = UserWorkshopService.get_user_workshops(current_user.id)
            for workshop in user_workshops.workshops:
                if workshop.workshop_id == registration_data.workshop_id:
                    log.warning(f"Duplicate registration attempt: user {current_user.id}, workshop {registration_data.workshop_id}")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="You are already registered for this workshop"
                    )
        except HTTPException as e:
            if e.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR:
                # If it's not a server error, user might have no workshops yet - continue
                pass
            else:
                raise e
        
        # Register user to workshop
        from app.schemas.user_workshop import RegisterUserToWorkshopSchema
        registration_payload = RegisterUserToWorkshopSchema(
            user_id=current_user.id,
            workshop_id=registration_data.workshop_id
        )
        
        result = UserWorkshopService.register_user_to_workshop(registration_payload)
        
        # Auto-create assignment for enrolled workshop
        assignment_created = await AssignmentService.create_assignment_on_enroll(
            current_user.id, 
            registration_data.workshop_id
        )
        
        if assignment_created:
            log.info(f"Assignment auto-created for user {current_user.id} in workshop {registration_data.workshop_id}")
        else:
            log.warning(f"Assignment creation failed for user {current_user.id} in workshop {registration_data.workshop_id}")
        
        response_data = RegistrationResponseSchema(
            user_id=result.user_id,
            workshop_id=result.workshop_id,
            registration_date=result.created_at,
            user_type="registered",
            message=f"Successfully registered for workshop and assignment created"
        )
        
        log.info(f"Registered user {current_user.email} successfully registered for workshop {registration_data.workshop_id}")
        
        return ResponseModel(
            message="Registration successful with assignment created",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error in registered user registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to internal error"
        )


# 🟡 Route 2: Guest Registration  
@router.post("/register/guest", response_model=ResponseModel[RegistrationResponseSchema])
async def register_guest_to_workshop(
    registration_data: GuestRegistrationSchema,
    guest_user: User = Depends(get_or_create_guest_account)
):
    """
    Register a guest user to a workshop
    - Creates guest account if email doesn't exist
    - Validates that registered users don't use this route
    - Prevents duplicate registrations
    - Auto-creates assignment for enrolled workshop
    """
    try:
        log.info(f"Guest user {registration_data.email} attempting to register for workshop {registration_data.workshop_id}")
        
        # Check for duplicate registration by trying to get user workshops
        try:
            user_workshops = UserWorkshopService.get_user_workshops(guest_user.id)
            for workshop in user_workshops.workshops:
                if workshop.workshop_id == registration_data.workshop_id:
                    log.warning(f"Duplicate registration attempt: guest {guest_user.id}, workshop {registration_data.workshop_id}")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="This email is already registered for this workshop"
                    )
        except HTTPException as e:
            if e.status_code != status.HTTP_500_INTERNAL_SERVER_ERROR:
                # If it's not a server error, user might have no workshops yet - continue
                pass
            else:
                raise e
        
        # Register guest to workshop
        from app.schemas.user_workshop import RegisterUserToWorkshopSchema
        registration_payload = RegisterUserToWorkshopSchema(
            user_id=guest_user.id,
            workshop_id=registration_data.workshop_id
        )
        
        result = UserWorkshopService.register_user_to_workshop(registration_payload)
        
        # Auto-create assignment for enrolled workshop
        assignment_created = await AssignmentService.create_assignment_on_enroll(
            guest_user.id, 
            registration_data.workshop_id
        )
        
        if assignment_created:
            log.info(f"Assignment auto-created for guest user {guest_user.id} in workshop {registration_data.workshop_id}")
        else:
            log.warning(f"Assignment creation failed for guest user {guest_user.id} in workshop {registration_data.workshop_id}")
        
        response_data = RegistrationResponseSchema(
            user_id=result.user_id,
            workshop_id=result.workshop_id,
            registration_date=result.created_at,
            user_type="guest",
            message=f"Successfully registered as guest for workshop and assignment created"
        )
        
        log.info(f"Guest user {registration_data.email} successfully registered for workshop {registration_data.workshop_id}")
        
        return ResponseModel(
            message="Guest registration successful with assignment created",
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error in guest registration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Guest registration failed due to internal error"
        )


# � Route 3: Get Workshop Participants (Admin Only)
@router.get("/workshop/{workshop_id}/participants", response_model=ResponseModel[FetchWorkshopUsersResponse])
def get_workshop_participants(
    workshop_id: UUID,
    _: str = Depends(require_admin)
):
    """
    Get all users (registered + guests) for a specific workshop
    - Admin access required
    - Returns complete participant list with user details
    """
    try:
        log.debug(f"Admin fetching participants for workshop: {workshop_id}")
        
        participants = UserWorkshopService.get_workshop_users(workshop_id)
        
        log.info(f"Retrieved {participants.total_participants} participants for workshop {workshop_id}")
        
        return ResponseModel(
            message=f"Found {participants.total_participants} participants",
            data=participants
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching workshop participants")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch workshop participants"
        )


# 👤 Route 4: Get User's Registered Workshops
@router.get("/user/workshops", response_model=ResponseModel[FetchUsersWorkshopsResponse])
def get_user_workshops(
    current_user: User = Depends(get_current_registered_user)
):
    """
    Get all workshops the current user is registered for
    - Requires authentication
    - Returns user's workshop history
    """
    try:
        log.debug(f"Fetching workshops for user: {current_user.email}")
        
        user_workshops = UserWorkshopService.get_user_workshops(current_user.id)
        
        log.info(f"Retrieved {user_workshops.total_workshops} workshops for user {current_user.email}")
        
        return ResponseModel(
            message=f"Found {user_workshops.total_workshops} registered workshops",
            data=user_workshops
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching user workshops")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your workshops"
        )


# 🔄 Route 5: Update Reminder Status (Admin Only)
@router.patch("/reminder-status", response_model=ResponseModel[UserWorkshopRelation])
def update_reminder_status(
    reminder_data: UpdateReminderStatusSchema,
    _: str = Depends(require_admin)
):
    """
    Update reminder status for a user-workshop registration
    - Admin access required
    - Used by reminder system
    """
    try:
        log.debug(f"Admin updating reminder status for user {reminder_data.user_id}, workshop {reminder_data.workshop_id}")
        
        updated_relation = UserWorkshopService.update_reminder_status(reminder_data)
        
        log.info(f"Reminder status updated for user {reminder_data.user_id}, workshop {reminder_data.workshop_id}")
        
        return ResponseModel(
            message="Reminder status updated successfully",
            data=updated_relation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error updating reminder status")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reminder status"
        )


# 🗑️ Route 6: Unregister from Workshop
@router.delete("/unregister/{workshop_id}", response_model=ResponseModel[dict])
def unregister_from_workshop(
    workshop_id: UUID,
    current_user: User = Depends(get_current_registered_user)
):
    """
    Unregister current user from a workshop
    - Requires authentication
    - User can only unregister themselves
    """
    try:
        log.info(f"User {current_user.email} attempting to unregister from workshop {workshop_id}")
        
        success = UserWorkshopService.unregister_user_from_workshop(current_user.id, workshop_id)
        
        if success:
            log.info(f"User {current_user.email} successfully unregistered from workshop {workshop_id}")
            return ResponseModel(
                message="Successfully unregistered from workshop",
                data={"user_id": str(current_user.id), "workshop_id": str(workshop_id), "status": "unregistered"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error unregistering from workshop")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unregister from workshop"
        )
