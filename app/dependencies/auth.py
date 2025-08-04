from fastapi import Depends, HTTPException, Request
from app.services.auth import AuthService
from app.schemas.user import UserRole, UserCreate, User
from pydantic import EmailStr

# 🔑 Extract token from Authorization header
def get_token_from_request(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing")
    return auth_header.split(" ")[1]

# 👤 Current user fetch/create dependency
async def get_current_user(request: Request) -> dict:
    token = get_token_from_request(request)
    
    try:
        user_data = AuthService.decode_token(token)
        
        # Single method handles all user logic (create/upgrade/fetch)
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

# 🛡️ Role checker for protected routes
def require_role(allowed_roles: list[UserRole]):
    async def checker(user: dict = Depends(get_current_user)):
        user_role = user.get("role")
        if user_role not in [role.value for role in allowed_roles]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker


require_admin = require_role([UserRole.admin])
require_user = require_role([UserRole.user, UserRole.admin])
