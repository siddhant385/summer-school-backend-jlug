# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException
from app.dependencies.auth import authenticate_and_create_user
from app.services.auth import AuthService
from app.core.logger import log
from pydantic import BaseModel


router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me")
async def get_user_profile(current_user: dict = Depends(authenticate_and_create_user)):
    """
    Frontend authentication endpoint - verifies token and creates/upgrades user.
    
    Header: Authorization: Bearer <your_jwt_token>
    
    This endpoint:
    - Verifies JWT token from Google OAuth
    - Creates user if first time 
    - Upgrades user if needed
    - Returns complete user profile
    
    Perfect for frontend's first connection after Google login!
    """
    return {
        "success": True,
        "message": "User authenticated successfully", 
        "data": current_user
    }
