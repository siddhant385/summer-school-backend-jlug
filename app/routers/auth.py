# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, Request
from app.dependencies.auth import get_current_user, get_token_from_request
from app.services.auth import AuthService
from app.schemas.user import User
from app.core.logger import log
from pydantic import BaseModel


router = APIRouter(prefix="/auth", tags=["Authentication"])

class TokenRequest(BaseModel):
    token: str

@router.post("/verify-token")
async def verify_token(token_request: TokenRequest):
    """
    Verify JWT token and return user info (alternative to automatic dependency).
    
    Use this when you want to manually send token in request body.
    """
    try:
        user_data = AuthService.decode_token(token_request.token)
        user = AuthService.get_or_create_user(
            email=user_data.email,
            auth_id=user_data.sub,
            metadata=user_data.user_metadata
        )
        
        return {
            "success": True,
            "message": "Token verified successfully",
            "user": user
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=401, detail=f"{e}")

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Get current user information from JWT token in Authorization header.
    
    Header format: Authorization: Bearer <your_jwt_token>
    
    This endpoint automatically:
    - Extracts token from Authorization header
    - Creates/upgrades user if needed
    - Returns complete user information
    """
    return {
        "success": True,
        "message": "User authenticated successfully", 
        "user": current_user
    }

@router.get("/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get user profile (same as /me but different endpoint).
    
    Header: Authorization: Bearer <your_jwt_token>
    """
    return {
        "success": True,
        "user": current_user
    }
