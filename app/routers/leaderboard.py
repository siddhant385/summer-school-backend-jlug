# app/routers/leaderboard.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional

from app.core.logger import setup_logger
from app.services.leaderboard import LeaderboardService
from app.schemas.leaderboard import (
    LeaderboardResponse, TopPerformersResponse, UserRankResponse, 
    LeaderboardFilters
)
from app.schemas.response import ResponseModel
from app.schemas.user import User
from app.dependencies.auth import verify_valid_token
from app.dependencies.user_workshop import get_current_registered_user

log = setup_logger(__name__)
router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

# 🏆 Route 1: Get Main Leaderboard (Authenticated Users Only)
@router.get("/", response_model=ResponseModel[LeaderboardResponse])
async def get_leaderboard(
    current_user: User = Depends(get_current_registered_user),
    limit: int = Query(20, ge=1, le=100, description="Number of users to fetch"),
    offset: int = Query(0, ge=0, description="Number of users to skip"),
    min_points: Optional[int] = Query(None, ge=0, description="Minimum points filter"),
    time_period: str = Query("all_time", description="Time period filter")
):
    """
    Get main leaderboard with current user's position
    - Requires authentication (no guest users)
    - Returns paginated leaderboard with user stats
    - Shows current user's rank and points
    - Supports filtering by minimum points
    """
    try:
        log.info(f"User {current_user.email} requesting leaderboard")
        
        # Validate time period
        valid_periods = ["all_time", "this_month", "this_week"]
        if time_period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid time period. Must be one of: {valid_periods}"
            )
        
        # Create filters
        filters = LeaderboardFilters(
            time_period=time_period,
            min_points=min_points,
            limit=limit,
            offset=offset
        )
        
        result = await LeaderboardService.get_main_leaderboard(current_user.id, filters)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        log.info(f"Leaderboard fetched for user {current_user.email}: {result.data.total_users} users")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching leaderboard")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch leaderboard"
        )

# 🥇 Route 2: Get Top Performers (Public for Homepage)
@router.get("/top", response_model=ResponseModel[TopPerformersResponse])
async def get_top_performers():
    """
    Get top 3 performers for homepage highlights
    - No authentication required
    - Returns top 3 users with highest points
    - Includes total participants count
    - Perfect for homepage/dashboard display
    """
    try:
        log.info("Fetching top performers for public display")
        
        result = await LeaderboardService.get_top_performers()
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        log.info(f"Top performers fetched: {len(result.data.top_three)} users")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching top performers")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch top performers"
        )

# 👤 Route 3: Get My Rank (Authenticated User's Personal Stats)
@router.get("/me", response_model=ResponseModel[UserRankResponse])
async def get_my_rank(
    current_user: User = Depends(get_current_registered_user)
):
    """
    Get current user's detailed rank and stats
    - Requires authentication
    - Returns user's rank, points, and activity stats
    - Shows position in leaderboard
    - Personal dashboard information
    """
    try:
        log.info(f"User {current_user.email} requesting their rank")
        
        result = await LeaderboardService.get_user_rank(current_user.id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        log.info(f"User rank fetched for {current_user.email}: Rank #{result.data.user_rank.rank}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching user rank")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your rank"
        )

# 🔍 Route 4: Get User Rank by ID (Admin or Self Only)
@router.get("/user/{user_id}", response_model=ResponseModel[UserRankResponse])
async def get_user_rank_by_id(
    user_id: str,
    current_user: User = Depends(get_current_registered_user)
):
    """
    Get specific user's rank and stats
    - Requires authentication
    - Users can only view their own rank or admins can view any
    - Returns detailed user rank information
    """
    try:
        from uuid import UUID
        target_user_id = UUID(user_id)
        
        # Check if user is requesting their own rank or is admin
        if current_user.id != target_user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own rank"
            )
        
        log.info(f"User {current_user.email} requesting rank for user {target_user_id}")
        
        result = await LeaderboardService.get_user_rank(target_user_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        log.info(f"User rank fetched for {target_user_id}: Rank #{result.data.user_rank.rank}")
        return result
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching user rank by ID")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user rank"
        )
