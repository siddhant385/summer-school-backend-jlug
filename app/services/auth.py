# app/services/auth.py

from uuid import UUID
from fastapi import HTTPException, status
from app.schemas.auth import TokenData, UserMetadata
from app.schemas.user import UserCreate, UserRoleUpgrade, UserRole
from app.core.config import settings
from app.core.db import get_db, get_db_admin
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError
from pydantic import EmailStr
from app.core.logger import setup_logger
# Load JWT secret key (assuming it is set in .env)
SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ALGORITHM = settings.ALGORITHM

log = setup_logger(__name__)
class AuthService:
    
    @staticmethod
    def decode_token(token: str) -> TokenData:
        """Decode JWT token and return TokenData."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],audience="authenticated")
            sub = payload.get("sub")
            email = payload.get("email")
            user_metadata = payload.get("user_metadata")

            if not sub or not email or not user_metadata:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return TokenData(sub=UUID(sub), email=email, user_metadata=user_metadata)
        except ExpiredSignatureError:
            log.error("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTClaimsError:
            log.error("Invalid token claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            log.error(f"JWT Error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from e

    @staticmethod
    def create_user_in_db(user_data: UserCreate) -> dict:
        """Create a new user in the database using UserCreate schema."""
        db = get_db_admin()
        try:
            log.debug(f"Creating user in database: {user_data.email}")
            
            user_dict = {
                "email": user_data.email,
                "name": user_data.name,
                "auth_id": str(user_data.auth_id) if user_data.auth_id else None,
                "profile_pic_url": user_data.profile_pic_url,
                "role": user_data.role.value,
                "points": user_data.points or 0,  # Default to 0 if not provided
            }
            
            response = db.table("users").insert(user_dict).execute()
            
            if not response.data:
                log.error(f"Failed to create user in database: {user_data.email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user in database"
                )
            
            log.debug(f"User created: {user_data.email}")
            return response.data[0]
            
        except Exception as e:
            log.error(f"Error creating user {user_data.email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}"
            )

    @staticmethod
    def upgrade_user_role(upgrade_data: UserRoleUpgrade, email: EmailStr) -> dict:
        """Upgrade user role using UserRoleUpgrade schema."""
        db = get_db_admin()
        try:
            log.debug(f"Upgrading user role for: {email}")
            
            # First check if user exists with this email
            existing_user = db.table("users").select("*").eq("email", email).execute()
            
            if not existing_user.data:
                log.warning(f"User not found for role upgrade: {email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Update with auth_id from schema and change role
            response = db.table("users").update({
                "auth_id": str(upgrade_data.auth_id),
                "role": upgrade_data.role.value
            }).eq("email", email).execute()
            
            if not response.data:
                log.error(f"Failed to update user role for: {email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user role"
                )
            
            log.info(f"User role upgraded: {email} -> {upgrade_data.role.value}")
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error updating user role for {email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user role: {str(e)}"
            )

    @staticmethod
    def upgrade_user_role_with_profile(upgrade_data: UserRoleUpgrade, email: EmailStr, name: str, profile_pic_url: str) -> dict:
        """Upgrade user role AND profile data (name, profile pic) - for guest to user upgrade."""
        db = get_db_admin()
        try:
            log.debug(f"Upgrading user role and profile for: {email}")
            
            # First check if user exists with this email
            existing_user = db.table("users").select("*").eq("email", email).execute()
            
            if not existing_user.data:
                log.warning(f"User not found for role upgrade: {email}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Update with auth_id, role, name, and profile pic
            update_data = {
                "auth_id": str(upgrade_data.auth_id),
                "role": upgrade_data.role.value,
                "name": name,
                "profile_pic_url": profile_pic_url
            }
            
            response = db.table("users").update(update_data).eq("email", email).execute()
            
            if not response.data:
                log.error(f"Failed to update user profile for: {email}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user profile"
                )
            
            log.info(f"User profile upgraded: {email} -> {upgrade_data.role.value} (name: {name})")
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error updating user profile for {email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user profile: {str(e)}"
            )

    @staticmethod
    def get_user_role(email: EmailStr) -> str:
        """Get user role from database using email."""
        db = get_db()
        try:
            response = db.table("users").select("role").eq("email", email).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            return response.data[0]["role"]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user role: {str(e)}"
            )

    @staticmethod
    def get_user_by_email(email: EmailStr) -> dict:
        """Get complete user data from database using email."""
        db = get_db()
        try:
            response = db.table("users").select("*").eq("email", email).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching user: {str(e)}"
            )

    @staticmethod
    def verify_user_exists(email: EmailStr) -> bool:
        """Verify if user exists in database using email."""
        db = get_db()
        try:
            response = db.table("users").select("email").eq("email", email).execute()
            return bool(response.data)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying user existence: {str(e)}"
            )

    @staticmethod
    def check_user_role(email: EmailStr, required_role: UserRole) -> bool:
        """Check if user has the required role using UserRole enum."""
        try:
            user_role = AuthService.get_user_role(email)
            return user_role == required_role.value
            
        except HTTPException:
            return False
        except Exception:
            return False

    @staticmethod
    def get_or_create_user(email: EmailStr, auth_id: UUID, metadata) -> dict:
        """Single method to handle user fetch/create/upgrade logic."""
        try:
            log.debug(f"Processing user authentication: {email}")
            
            if AuthService.verify_user_exists(email):
                current_role = AuthService.get_user_role(email)
                
                if current_role == "guest":
                    # Auto-upgrade guest to user with complete profile data
                    log.debug(f"Auto-upgrading guest user: {email}")
                    from app.schemas.user import UserRoleUpgrade
                    
                    # Include profile data in upgrade
                    upgrade_data = UserRoleUpgrade(auth_id=auth_id, role=UserRole.user)
                    return AuthService.upgrade_user_role_with_profile(
                        upgrade_data=upgrade_data,
                        email=email,
                        name=metadata.name,
                        profile_pic_url=metadata.avatar_url
                    )
                else:
                    log.debug(f"Returning existing user: {email}")
                    return AuthService.get_user_by_email(email)
            else:
                # Create new user
                log.debug(f"Creating new user: {email}")
                from app.schemas.user import UserCreate
                user_data = UserCreate(
                    email=email,
                    name=metadata.name,
                    auth_id=auth_id,
                    profile_pic_url=metadata.avatar_url,
                    role=UserRole.user,
                    points=0  # Default points for new users
                )
                return AuthService.create_user_in_db(user_data)
                
        except Exception as e:
            log.error(f"Error processing user {email}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing user: {str(e)}"
            )
