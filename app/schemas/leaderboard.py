# app/schemas/leaderboard.py
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime

# Core leaderboard entry model
class LeaderboardEntry(BaseModel):
    """Single user entry in leaderboard"""
    rank: int
    user_id: UUID
    name: str
    points: int
    profile_pic_url: Optional[str] = None
    
    # Additional stats for better UX
    assignments_completed: Optional[int] = 0
    workshops_attended: Optional[int] = 0
    certificates_earned: Optional[int] = 0
    
    model_config = ConfigDict(from_attributes=True)

# Leaderboard response models
class LeaderboardResponse(BaseModel):
    """Main leaderboard response"""
    entries: List[LeaderboardEntry]
    total_users: int
    current_user_rank: Optional[int] = None  # User's own rank if authenticated
    current_user_points: Optional[int] = None  # User's own points if authenticated
    
    # Pagination info
    page: int = 1
    limit: int = 10
    has_next: bool = False
    has_previous: bool = False

# Top performers response (for highlights)
class TopPerformersResponse(BaseModel):
    """Top 3 performers for special display"""
    top_three: List[LeaderboardEntry]
    total_participants: int
    highest_points: int

# User rank response (for individual lookup)
class UserRankResponse(BaseModel):
    """Individual user's rank and stats"""
    user_rank: LeaderboardEntry
    rank_change: Optional[int] = None  # +5 or -3 etc (compared to last week/month)
    points_this_week: Optional[int] = 0
    points_this_month: Optional[int] = 0
    
# Leaderboard filters/params
class LeaderboardFilters(BaseModel):
    """Filters for leaderboard queries"""
    time_period: Optional[str] = "all_time"  # all_time, this_month, this_week
    min_points: Optional[int] = None
    limit: int = 20
    offset: int = 0
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "time_period": "all_time",
                "min_points": 10,
                "limit": 20,
                "offset": 0
            }
        }
    )
