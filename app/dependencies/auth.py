from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth import AuthService
from app.schemas.user import UserRole, UserCreate, User
from app.core.logger import setup_logger
from pydantic import EmailStr
from uuid import UUID

# 🔑 FastAPI inbuilt security scheme for Bearer tokens
bearer_scheme = HTTPBearer()
log = setup_logger(__name__)

# 🔐 Dependency 1: Just verify token is valid (lightweight)
async def verify_valid_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Verify JWT token is valid and return email"""
    try:
        user_data = AuthService.decode_token(credentials.credentials)
        log.debug(f"Token verified for user: {user_data.email}")
        return user_data.email
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Token verification failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")

# 🛡️ Dependency 2: Verify token + check admin role
async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Verify token AND ensure user is admin"""
    try:
        user_data = AuthService.decode_token(credentials.credentials)
        user_role = AuthService.get_user_role(user_data.email)
        
        if user_role != UserRole.admin.value:
            log.warning(f"Admin access denied for user {user_data.email} with role {user_role}")
            raise HTTPException(
                status_code=403, 
                detail=f"Admin access required. Current role: {user_role}"
            )
        
        log.debug(f"Admin access granted to: {user_data.email}")
        return user_data.email
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Admin verification failed: {str(e)}")
        raise HTTPException(status_code=403, detail="Admin verification failed")

# 👤 Dependency 3: Full user authentication with creation/upgrade logic
async def authenticate_and_create_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> User:
    """Complete authentication with user creation/upgrade - for first-time auth"""
    try:
        user_data = AuthService.decode_token(credentials.credentials)
        
        # Handle user creation/upgrade logic
        user_dict = AuthService.get_or_create_user(
            email=user_data.email,
            auth_id=user_data.sub,
            metadata=user_data.user_metadata
        )
        
        if not user_dict:
            log.error(f"Failed to process user for email: {user_data.email}")
            raise HTTPException(status_code=500, detail="Failed to process user")
        
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
            profile_complete=user_dict.get("profile_complete", False)  # Keep as False - user needs to complete manually
        )
        
        log.debug(f"User authenticated: {user.email} (role: {user.role})")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Authentication failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")
