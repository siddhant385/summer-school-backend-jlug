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
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user in database"
                )
                
            return response.data[0]
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating user: {str(e)}"
            )

    @staticmethod
    def upgrade_user_role(upgrade_data: UserRoleUpgrade, email: EmailStr) -> dict:
        """Upgrade user role using UserRoleUpgrade schema."""
        db = get_db_admin()
        try:
            # First check if user exists with this email
            existing_user = db.table("users").select("*").eq("email", email).execute()
            
            if not existing_user.data:
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
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user role"
                )
                
            return response.data[0]
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating user role: {str(e)}"
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
            if AuthService.verify_user_exists(email):
                current_role = AuthService.get_user_role(email)
                
                if current_role == "guest":
                    # Auto-upgrade guest to user
                    from app.schemas.user import UserRoleUpgrade
                    upgrade_data = UserRoleUpgrade(auth_id=auth_id, role=UserRole.user)
                    return AuthService.upgrade_user_role(upgrade_data, email)
                else:
                    return AuthService.get_user_by_email(email)
            else:
                # Create new user
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing user: {str(e)}"
            )
