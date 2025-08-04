from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth import AuthService
from app.schemas.user import UserRole, UserCreate, User
from pydantic import EmailStr

# 🔑 FastAPI inbuilt security scheme for Bearer tokens
bearer_scheme = HTTPBearer()

# 🔐 Dependency 1: Just verify token is valid (lightweight)
async def verify_valid_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Verify JWT token is valid and return email"""
    try:
        user_data = AuthService.decode_token(credentials.credentials)
        return user_data.email
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# 🛡️ Dependency 2: Verify token + check admin role
async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """Verify token AND ensure user is admin"""
    try:
        user_data = AuthService.decode_token(credentials.credentials)
        user_role = AuthService.get_user_role(user_data.email)
        
        if user_role != UserRole.admin.value:
            raise HTTPException(
                status_code=403, 
                detail=f"Admin access required. Current role: {user_role}"
            )
        return user_data.email
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=403, detail="Admin verification failed")

# 👤 Dependency 3: Full user authentication with creation/upgrade logic
async def authenticate_and_create_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> User:
    """Complete authentication with user creation/upgrade - for first-time auth"""
    try:
        user_data = AuthService.decode_token(credentials.credentials)
        
        # Handle user creation/upgrade logic
        user = AuthService.get_or_create_user(
            email=user_data.email,
            auth_id=user_data.sub,
            metadata=user_data.user_metadata
        )
        
        if not user:
            raise HTTPException(status_code=500, detail="Failed to process user")
            
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")
