# app/dependencies/user_workshop.py

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from uuid import UUID
from pydantic import EmailStr

from app.core.logger import setup_logger
from app.services.auth import AuthService
from app.services.user_workshop import UserWorkshopService
from app.schemas.user import User, UserRole, UserCreate
from app.schemas.user_workshop import RegisterUserToWorkshopSchema

# 🔑 FastAPI security scheme
bearer_scheme = HTTPBearer()
log = setup_logger(__name__)


class WorkshopRegistrationDependencies:
    """Dependencies for workshop registration workflows"""

    # 🟢 Dependency 1: Get Current Registered User (for registered user route)
    @staticmethod
    async def get_current_registered_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
    ) -> User:
        """
        Get current authenticated registered user (not guest)
        Used for: /register/registered-user route
        """
        try:
            log.debug("Extracting current registered user from token")
            
            # Decode token
            user_data = AuthService.decode_token(credentials.credentials)
            
            # Get user details
            user_dict = AuthService.get_or_create_user(
                email=user_data.email,
                auth_id=user_data.sub,
                metadata=user_data.user_metadata
            )
            
            if not user_dict:
                log.error(f"Failed to get user details for: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process user"
                )
            
            # Convert dict to User object
            user = User(
                id=UUID(user_dict["id"]),
                email=user_dict["email"],
                name=user_dict["name"],
                auth_id=UUID(user_dict["auth_id"]) if user_dict.get("auth_id") else None,
                profile_pic_url=user_dict.get("profile_pic_url"),
                role=user_dict["role"],
                points=user_dict.get("points", 0),
                created_at=user_dict["created_at"],
                profile_complete=user_dict.get("profile_complete", False)
            )
            
            # Ensure user is not a guest
            if user.role == UserRole.guest.value:
                log.warning(f"Guest user {user.email} tried to use registered user route")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Guest users must use the guest registration route"
                )
            
            log.debug(f"Current registered user: {user.email} (role: {user.role})")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            log.exception(f"Error getting current registered user")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

    # 🟡 Dependency 2: Check Existing User by Email (for guest route validation)
    @staticmethod
    async def check_existing_user_by_email(email: EmailStr) -> Optional[User]:
        """
        Check if user with given email already exists
        Used for: Guest registration validation
        Returns: User object if exists, None if not found
        """
        try:
            log.debug(f"Checking if user exists for email: {email}")
            
            # Try to get existing user - handle 404 properly
            try:
                existing_user_dict = AuthService.get_user_by_email(email)
                
                # Convert dict to User object
                existing_user = User(
                    id=UUID(existing_user_dict["id"]),
                    email=existing_user_dict["email"],
                    name=existing_user_dict["name"],
                    auth_id=UUID(existing_user_dict["auth_id"]) if existing_user_dict.get("auth_id") else None,
                    profile_pic_url=existing_user_dict.get("profile_pic_url"),
                    role=existing_user_dict["role"],
                    points=existing_user_dict.get("points", 0),
                    created_at=existing_user_dict["created_at"],
                    profile_complete=existing_user_dict.get("profile_complete", False)
                )
                
                log.debug(f"Found existing user: {email} (role: {existing_user.role})")
                return existing_user
                
            except HTTPException as e:
                # If 404, user doesn't exist - return None
                if e.status_code == 404:
                    log.debug(f"No existing user found for email: {email}")
                    return None
                # For other HTTP errors, re-raise
                raise e
            
        except Exception as e:
            log.exception(f"Error checking existing user for email: {email}")
            # Don't raise exception here, let the caller handle None return
            return None

    # 🔧 Dependency 3: Validate Guest Registration Request
    @staticmethod
    async def validate_guest_registration(
        email: EmailStr
    ) -> dict:
        """
        Validate guest registration request and return validation info
        Used for: /register/guest route validation
        """
        try:
            log.debug(f"Validating guest registration for email: {email}")
            
            # Get existing user manually (no Depends here)
            existing_user = await WorkshopRegistrationDependencies.check_existing_user_by_email(email)
            
            validation_result = {
                "can_register": False,
                "existing_user": existing_user,
                "action_needed": None,
                "error_message": None
            }
            
            if existing_user:
                # If user exists and is NOT a guest (registered user)
                if existing_user.role != UserRole.guest.value:
                    log.warning(f"Registered user {email} tried to use guest registration")
                    validation_result["error_message"] = (
                        "This email is already associated with a registered account. "
                        "Please log in and register for the workshop."
                    )
                    return validation_result
                
                # If user exists and IS a guest - can proceed
                log.debug(f"Existing guest user found: {email}")
                validation_result["can_register"] = True
                validation_result["action_needed"] = "check_duplicate_registration"
                
            else:
                # No user exists - need to create guest account
                log.debug(f"New guest user registration: {email}")
                validation_result["can_register"] = True
                validation_result["action_needed"] = "create_guest_account"
            
            return validation_result
            
        except Exception as e:
            log.exception(f"Error validating guest registration for: {email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate registration request"
            )

    # 🔒 Dependency 4: Check Workshop Registration Duplication
    @staticmethod
    async def check_registration_duplicate(
        user_id: UUID,
        workshop_id: UUID
    ) -> bool:
        """
        Check if user is already registered for workshop
        Returns: True if already registered, False if not
        """
        try:
            log.debug(f"Checking registration duplicate for user {user_id}, workshop {workshop_id}")
            
            # Try to get existing registration
            try:
                existing_workshops = UserWorkshopService.get_user_workshops(user_id)
                
                # Check if workshop_id exists in user's workshops
                for workshop in existing_workshops.workshops:
                    if workshop.workshop_id == workshop_id:
                        log.warning(f"Duplicate registration found: user {user_id}, workshop {workshop_id}")
                        return True
                
                log.debug(f"No duplicate registration found")
                return False
                
            except HTTPException as e:
                # If 500 error, re-raise. If 404, user has no workshops yet
                if e.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
                    raise e
                return False
                
        except Exception as e:
            log.exception(f"Error checking registration duplicate")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to check registration status"
            )

    # 🎯 Dependency 5: Create Guest Account if Needed
    @staticmethod
    async def get_or_create_guest_account(
        name: str,
        email: EmailStr
    ) -> User:
        """
        Get existing guest user or create new guest account
        Used for: Guest registration flow
        """
        try:
            log.debug(f"Getting or creating guest account for: {email}")
            
            # Get validation result manually
            validation_result = await WorkshopRegistrationDependencies.validate_guest_registration(email)
            
            # Check validation result
            if not validation_result["can_register"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=validation_result["error_message"]
                )
            
            # If existing guest user, return it
            if validation_result["existing_user"]:
                log.debug(f"Returning existing guest user: {email}")
                return validation_result["existing_user"]
            
            # Create new guest account
            log.debug(f"Creating new guest account for: {email}")
            
            guest_data = UserCreate(
                email=email,
                name=name,
                role=UserRole.guest,
                profile_complete=False
            )
            
            new_guest = AuthService.create_user_in_db(guest_data)
            
            if not new_guest:
                log.error(f"Failed to create guest account for: {email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create guest account"
                )
            
            # Convert dict to User object
            guest_user = User(
                id=UUID(new_guest["id"]),
                email=new_guest["email"],
                name=new_guest["name"],
                auth_id=UUID(new_guest["auth_id"]) if new_guest.get("auth_id") else None,
                profile_pic_url=new_guest.get("profile_pic_url"),
                role=new_guest["role"],
                points=new_guest.get("points", 0),
                created_at=new_guest["created_at"],
                profile_complete=False  # Default for new guest accounts
            )
            
            log.info(f"New guest account created: {email}")
            return guest_user
            
        except HTTPException:
            raise
        except Exception as e:
            log.exception(f"Error creating guest account for: {email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create guest account"
            )


# 📌 Convenience aliases for easier imports
get_current_registered_user = WorkshopRegistrationDependencies.get_current_registered_user
check_existing_user_by_email = WorkshopRegistrationDependencies.check_existing_user_by_email
validate_guest_registration = WorkshopRegistrationDependencies.validate_guest_registration
check_registration_duplicate = WorkshopRegistrationDependencies.check_registration_duplicate
get_or_create_guest_account = WorkshopRegistrationDependencies.get_or_create_guest_account
