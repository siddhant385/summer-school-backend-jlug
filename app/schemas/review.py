# app/schemas/review.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Annotated
from app.schemas.user import User

class ReviewBase(BaseModel):
    """Shared fields for review creation and updates."""
    rating: Annotated[int, Field(ge=1, le=5, description="Rating from 1 to 5 stars")]
    review_description: Optional[str] = Field(None, max_length=1000, description="Review text content")


class ReviewCreate(ReviewBase):
    """Schema for creating a new review."""
    workshop_id: UUID = Field(..., description="Workshop being reviewed")
    # user_id will be extracted from JWT, not from request body


class ReviewUpdate(BaseModel):
    """Schema for updating existing review (rating and description only)."""
    rating: Optional[Annotated[int, Field(ge=1, le=5)]] = Field(None, description="Updated rating")
    review_description: Optional[str] = Field(None, max_length=1000, description="Updated review text")


class Review(BaseModel):
    """Complete review model matching database structure."""
    id: int  # bigint in database
    created_at: datetime
    review_description: Optional[str] = None
    rating: Optional[int] = None
    user_id: Optional[UUID] = None
    workshop_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class ReviewWithUser(BaseModel):
    """Review with user information for detailed responses."""
    id: int
    created_at: datetime
    review_description: Optional[str] = None
    rating: Optional[int] = None
    workshop_id: Optional[UUID] = None
    user: Optional[User] = None

    class Config:
        from_attributes = True


class ReviewOperationResponse(BaseModel):
    """Response for review create/update operations."""
    review: Review
    message: str = "Review operation completed successfully"


class ReviewListResponse(BaseModel):
    """Response for listing reviews with pagination."""
    reviews: List[ReviewWithUser]
    total_count: int
    workshop_id: Optional[UUID] = None
    average_rating: Optional[float] = None


class WorkshopReviewSummary(BaseModel):
    """Summary of reviews for a workshop."""
    workshop_id: UUID
    total_reviews: int
    average_rating: float
    rating_distribution: dict  # {1: count, 2: count, 3: count, 4: count, 5: count}
    recent_reviews: List[ReviewWithUser]
