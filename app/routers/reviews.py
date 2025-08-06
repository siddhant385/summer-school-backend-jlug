# app/routers/reviews.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.logger import setup_logger
from app.core.db import get_db
from app.services.review import review_service
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewOperationResponse, 
    ReviewListResponse, Review
)
from app.schemas.response import ResponseModel
from app.dependencies.auth import authenticate_and_create_user, require_admin
from app.schemas.user import User
from uuid import UUID
from supabase import Client
from typing import Dict

log = setup_logger(__name__)
router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ResponseModel[ReviewOperationResponse])
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(authenticate_and_create_user),
    db: Client = Depends(get_db)
):
    """Create a new review for a workshop"""
    try:
        result = await review_service.create_review(review_data, current_user.id, db)
        if not result.success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.message)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error creating review: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create review")

@router.put("/{review_id}", response_model=ResponseModel[ReviewOperationResponse])
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    current_user: User = Depends(authenticate_and_create_user),
    db: Client = Depends(get_db)
):
    """Update your own review"""
    try:
        if review_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review ID")
        
        result = await review_service.update_review(review_id, review_data, current_user.id, db)
        if not result.success:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in result.message.lower() else status.HTTP_400_BAD_REQUEST
            raise HTTPException(status_code=status_code, detail=result.message)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error updating review: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update review")

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    admin_email: str = Depends(require_admin),
    db: Client = Depends(get_db)
):
    """Delete any review (admin only)"""
    try:
        if review_id <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review ID")
        
        # Get admin user for proper logging
        from app.services.auth import AuthService
        try:
            admin_user_data = AuthService.get_user_by_email(admin_email)
            admin_user_id = UUID(admin_user_data["id"]) if admin_user_data else None
        except:
            admin_user_id = None
        
        result = await review_service.delete_review(review_id, admin_user_id, is_admin=True, db=db)
        if not result.success:
            status_code = status.HTTP_404_NOT_FOUND if "not found" in result.message.lower() else status.HTTP_400_BAD_REQUEST
            raise HTTPException(status_code=status_code, detail=result.message)
        
        return None  # 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error deleting review: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete review")

@router.get("/workshops/{workshop_id}", response_model=ResponseModel[ReviewListResponse])
async def get_workshop_reviews(
    workshop_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Number of reviews per page"),
    offset: int = Query(0, ge=0, description="Number of reviews to skip"),
    db: Client = Depends(get_db)
):
    """Get all reviews for a workshop (public access)"""
    try:
        result = await review_service.get_reviews_by_workshop(workshop_id, limit, offset, db)
        if not result.success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.message)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting workshop reviews: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get reviews")

@router.get("/workshops/{workshop_id}/stats", response_model=ResponseModel[Dict])
async def get_workshop_rating_stats(
    workshop_id: UUID,
    db: Client = Depends(get_db)
):
    """Get rating statistics for a workshop"""
    try:
        result = await review_service.get_average_rating(workshop_id, db)
        if not result.success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.message)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting rating stats: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get rating statistics")

@router.get("/my-reviews", response_model=ResponseModel[ReviewListResponse])
async def get_my_reviews(
    current_user: User = Depends(authenticate_and_create_user),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews per page"),
    offset: int = Query(0, ge=0, description="Number of reviews to skip"),
    db: Client = Depends(get_db)
):
    """Get your own reviews"""
    try:
        result = await review_service.get_reviews_by_user(current_user.id, limit, offset, db)
        if not result.success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.message)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting user reviews: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get your reviews")

@router.get("/user/{user_id}", response_model=ResponseModel[ReviewListResponse])
async def get_user_reviews(
    user_id: UUID,
    admin_email: str = Depends(require_admin),
    limit: int = Query(20, ge=1, le=100, description="Number of reviews per page"),
    offset: int = Query(0, ge=0, description="Number of reviews to skip"),
    db: Client = Depends(get_db)
):
    """Get reviews by specific user (admin only)"""
    try:
        result = await review_service.get_reviews_by_user(user_id, limit, offset, db)
        if not result.success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.message)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error getting user reviews: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user reviews")


