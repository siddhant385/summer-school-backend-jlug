# app/services/leaderboard.py
from app.core.logger import setup_logger
from app.core.db import get_db
from app.schemas.leaderboard import (
    LeaderboardEntry, LeaderboardResponse, TopPerformersResponse, 
    UserRankResponse, LeaderboardFilters
)
from app.schemas.response import ResponseModel
from uuid import UUID
from typing import List, Optional, Dict, Any
from fastapi.concurrency import run_in_threadpool
from fastapi import HTTPException, status
from supabase import Client

log = setup_logger(__name__)

class LeaderboardService:
    """Service for leaderboard operations - authenticated users only"""
    
    @staticmethod
    async def get_main_leaderboard(
        current_user_id: UUID, 
        filters: LeaderboardFilters
    ) -> ResponseModel[LeaderboardResponse]:
        """Get main leaderboard with current user's position"""
        try:
            db = get_db()
            
            log.debug(f"Fetching leaderboard for user {current_user_id} with filters: {filters.model_dump()}")
            
            # Build query with filters
            query = db.table("users").select("""
                id,
                name,
                points,
                profile_pic_url,
                profile_complete
            """).eq("profile_complete", True)  # Only completed profiles
            
            # Apply minimum points filter
            if filters.min_points is not None:
                query = query.gte("points", filters.min_points)
            
            # Apply time period filter (for future enhancement)
            # For now, we'll use all-time points
            
            # Execute query with ordering and pagination
            result = await run_in_threadpool(
                lambda: query.order("points", desc=True)
                .range(filters.offset, filters.offset + filters.limit - 1).execute()
            )
            
            if not result.data:
                return ResponseModel(
                    success=True,
                    message="No users found for leaderboard",
                    data=LeaderboardResponse(
                        entries=[],
                        total_users=0,
                        current_user_rank=None,
                        current_user_points=None,
                        page=filters.offset // filters.limit + 1,
                        limit=filters.limit,
                        has_next=False,
                        has_previous=filters.offset > 0
                    )
                )
            
            # Get total count for pagination
            count_result = await run_in_threadpool(
                lambda: db.table("users").select("id", count="exact")
                .eq("profile_complete", True)
                .gte("points", filters.min_points or 0).execute()
            )
            total_users = count_result.count or 0
            
            # Create leaderboard entries with stats
            entries = []
            for index, user_data in enumerate(result.data):
                # Get user stats (assignments, workshops, certificates)
                stats = await LeaderboardService._get_user_stats(UUID(user_data["id"]))
                
                entry = LeaderboardEntry(
                    rank=filters.offset + index + 1,
                    user_id=UUID(user_data["id"]),
                    name=user_data.get("name", "Anonymous"),
                    points=user_data.get("points", 0),
                    profile_pic_url=user_data.get("profile_pic_url"),
                    assignments_completed=stats.get("assignments", 0),
                    workshops_attended=stats.get("workshops", 0),
                    certificates_earned=stats.get("certificates", 0)
                )
                entries.append(entry)
            
            # Get current user's rank and points
            current_user_rank, current_user_points = await LeaderboardService._get_user_rank(current_user_id)
            
            # Pagination info
            has_next = (filters.offset + filters.limit) < total_users
            has_previous = filters.offset > 0
            
            response_data = LeaderboardResponse(
                entries=entries,
                total_users=total_users,
                current_user_rank=current_user_rank,
                current_user_points=current_user_points,
                page=filters.offset // filters.limit + 1,
                limit=filters.limit,
                has_next=has_next,
                has_previous=has_previous
            )
            
            log.info(f"Leaderboard fetched: {len(entries)} entries, user rank: {current_user_rank}")
            
            return ResponseModel(
                success=True,
                message=f"Leaderboard fetched successfully ({len(entries)} users)",
                data=response_data
            )
            
        except Exception as e:
            log.error(f"Error fetching leaderboard: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch leaderboard"
            )
    
    @staticmethod
    async def get_top_performers() -> ResponseModel[TopPerformersResponse]:
        """Get top 3 performers for highlights (public endpoint)"""
        try:
            db = get_db()
            
            log.debug("Fetching top 3 performers")
            
            # Get top 3 users with highest points
            result = await run_in_threadpool(
                lambda: db.table("users").select("""
                    id,
                    name,
                    points,
                    profile_pic_url
                """).eq("profile_complete", True)
                .order("points", desc=True)
                .limit(3).execute()
            )
            
            if not result.data:
                return ResponseModel(
                    success=True,
                    message="No top performers found",
                    data=TopPerformersResponse(
                        top_three=[],
                        total_participants=0,
                        highest_points=0
                    )
                )
            
            # Get total participants count
            count_result = await run_in_threadpool(
                lambda: db.table("users").select("id", count="exact")
                .eq("profile_complete", True)
                .gt("points", 0).execute()
            )
            total_participants = count_result.count or 0
            
            # Create top performers entries
            top_three = []
            highest_points = 0
            
            for index, user_data in enumerate(result.data):
                stats = await LeaderboardService._get_user_stats(UUID(user_data["id"]))
                
                entry = LeaderboardEntry(
                    rank=index + 1,
                    user_id=UUID(user_data["id"]),
                    name=user_data.get("name", "Anonymous"),
                    points=user_data.get("points", 0),
                    profile_pic_url=user_data.get("profile_pic_url"),
                    assignments_completed=stats.get("assignments", 0),
                    workshops_attended=stats.get("workshops", 0),
                    certificates_earned=stats.get("certificates", 0)
                )
                top_three.append(entry)
                
                if index == 0:  # Highest points from #1 user
                    highest_points = user_data.get("points", 0)
            
            response_data = TopPerformersResponse(
                top_three=top_three,
                total_participants=total_participants,
                highest_points=highest_points
            )
            
            log.info(f"Top performers fetched: {len(top_three)} users, highest: {highest_points}")
            
            return ResponseModel(
                success=True,
                message="Top performers fetched successfully",
                data=response_data
            )
            
        except Exception as e:
            log.error(f"Error fetching top performers: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch top performers"
            )
    
    @staticmethod
    async def get_user_rank(user_id: UUID) -> ResponseModel[UserRankResponse]:
        """Get specific user's rank and detailed stats"""
        try:
            db = get_db()
            
            log.debug(f"Fetching rank for user: {user_id}")
            
            # Get user's current rank and points
            rank, points = await LeaderboardService._get_user_rank(user_id)
            
            if rank is None:
                return ResponseModel(
                    success=False,
                    message="User not found in leaderboard or profile incomplete",
                    data=None
                )
            
            # Get user details
            user_result = await run_in_threadpool(
                lambda: db.table("users").select("""
                    id,
                    name,
                    points,
                    profile_pic_url
                """).eq("id", str(user_id)).single().execute()
            )
            
            if not user_result.data:
                return ResponseModel(
                    success=False,
                    message="User not found",
                    data=None
                )
            
            user_data = user_result.data
            stats = await LeaderboardService._get_user_stats(user_id)
            
            # Create user rank entry
            user_rank_entry = LeaderboardEntry(
                rank=rank,
                user_id=user_id,
                name=user_data.get("name", "Anonymous"),
                points=points,
                profile_pic_url=user_data.get("profile_pic_url"),
                assignments_completed=stats.get("assignments", 0),
                workshops_attended=stats.get("workshops", 0),
                certificates_earned=stats.get("certificates", 0)
            )
            
            response_data = UserRankResponse(
                user_rank=user_rank_entry,
                rank_change=None,  # Future enhancement for tracking changes
                points_this_week=0,  # Future enhancement for time-based tracking
                points_this_month=0  # Future enhancement for time-based tracking
            )
            
            log.info(f"User rank fetched: {user_id} - Rank #{rank} with {points} points")
            
            return ResponseModel(
                success=True,
                message=f"User rank: #{rank} with {points} points",
                data=response_data
            )
            
        except Exception as e:
            log.error(f"Error fetching user rank {user_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch user rank"
            )
    
    @staticmethod
    async def _get_user_rank(user_id: UUID) -> tuple[Optional[int], Optional[int]]:
        """Helper method to get user's rank and points"""
        try:
            db = get_db()
            
            # Get user's points first
            user_result = await run_in_threadpool(
                lambda: db.table("users").select("points")
                .eq("id", str(user_id))
                .eq("profile_complete", True).execute()
            )
            
            if not user_result.data:
                return None, None
            
            user_points = user_result.data[0].get("points", 0)
            
            # Count users with higher points to determine rank
            rank_result = await run_in_threadpool(
                lambda: db.table("users").select("id", count="exact")
                .eq("profile_complete", True)
                .gt("points", user_points).execute()
            )
            
            rank = (rank_result.count or 0) + 1  # +1 because rank starts from 1
            
            return rank, user_points
            
        except Exception as e:
            log.error(f"Error getting user rank: {str(e)}")
            return None, None
    
    @staticmethod
    async def _get_user_stats(user_id: UUID) -> Dict[str, int]:
        """Helper method to get user's activity stats"""
        try:
            db = get_db()
            
            # Get assignments completed count
            assignments_result = await run_in_threadpool(
                lambda: db.table("assignments").select("id", count="exact")
                .eq("user_id", str(user_id))
                .eq("status", "submitted").execute()
            )
            assignments_count = assignments_result.count or 0
            
            # Get workshops attended count
            workshops_result = await run_in_threadpool(
                lambda: db.table("user_workshop").select("user_id", count="exact")
                .eq("user_id", str(user_id)).execute()
            )
            workshops_count = workshops_result.count or 0
            
            # Get certificates earned count
            certificates_result = await run_in_threadpool(
                lambda: db.table("certificates").select("id", count="exact")
                .eq("user_id", str(user_id)).execute()
            )
            certificates_count = certificates_result.count or 0
            
            return {
                "assignments": assignments_count,
                "workshops": workshops_count,
                "certificates": certificates_count
            }
            
        except Exception as e:
            log.error(f"Error getting user stats: {str(e)}")
            return {"assignments": 0, "workshops": 0, "certificates": 0}
