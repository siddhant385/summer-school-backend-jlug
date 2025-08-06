# app/services/review.py
from app.core.logger import setup_logger
from app.core.db import get_db
from app.schemas.review import (
    Review, ReviewCreate, ReviewUpdate, ReviewWithUser, 
    ReviewOperationResponse, ReviewListResponse
)
from app.schemas.response import ResponseModel
from app.schemas.user import User
from app.core.utils.bad_words import validate_review_content
from uuid import UUID
from typing import List, Optional, Dict
from fastapi.concurrency import run_in_threadpool
from supabase import Client

log = setup_logger(__name__)

# Constants
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

class ReviewService:
    
    def _validate_pagination(self, limit: int, offset: int) -> tuple[int, int]:
        """Validate pagination parameters"""
        limit = max(1, min(limit, MAX_LIMIT))
        offset = max(0, offset)
        return limit, offset

    async def create_review(self, review_data: ReviewCreate, user_id: UUID, db: Client) -> ResponseModel[ReviewOperationResponse]:
        """Create a new review for a workshop"""
        try:
            # Content validation
            if review_data.review_description:
                validation = validate_review_content(review_data.review_description)
                if not validation["is_valid"]:
                    return ResponseModel(
                        success=False,
                        message=f"Review validation failed: {', '.join(validation['errors'])}",
                        data=None
                    )

            # Check existing review
            existing = await run_in_threadpool(
                lambda: db.table("reviews").select("id").eq("user_id", str(user_id))
                .eq("workshop_id", str(review_data.workshop_id)).execute()
            )

            if existing.data:
                return ResponseModel(
                    success=False,
                    message="You have already reviewed this workshop",
                    data=None
                )

            # Create review
            review_dict = {
                "user_id": str(user_id),
                "workshop_id": str(review_data.workshop_id),
                "rating": review_data.rating,
                "review_description": review_data.review_description
            }

            result = await run_in_threadpool(
                lambda: db.table("reviews").insert(review_dict).execute()
            )
            
            if not result.data:
                return ResponseModel(success=False, message="Failed to create review", data=None)

            review = Review(**result.data[0])
            log.info(f"Review created: {review.id} by user {user_id}")

            return ResponseModel(
                success=True,
                message="Review created successfully",
                data=ReviewOperationResponse(review=review, message="Review added successfully")
            )

        except Exception as e:
            log.error(f"Error creating review: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    async def update_review(self, review_id: int, review_data: ReviewUpdate, user_id: UUID, db: Client) -> ResponseModel[ReviewOperationResponse]:
        """Update user's own review"""
        try:
            # Content validation
            if review_data.review_description:
                validation = validate_review_content(review_data.review_description)
                if not validation["is_valid"]:
                    return ResponseModel(
                        success=False,
                        message=f"Review validation failed: {', '.join(validation['errors'])}",
                        data=None
                    )

            # Check ownership
            existing = await run_in_threadpool(
                lambda: db.table("reviews").select("*").eq("id", review_id)
                .eq("user_id", str(user_id)).execute()
            )

            if not existing.data:
                return ResponseModel(
                    success=False,
                    message="Review not found or access denied",
                    data=None
                )

            # Build update dict
            update_dict = {}
            if review_data.rating is not None:
                update_dict["rating"] = review_data.rating
            if review_data.review_description is not None:
                update_dict["review_description"] = review_data.review_description

            if not update_dict:
                return ResponseModel(success=False, message="No fields to update", data=None)

            # Update review
            result = await run_in_threadpool(
                lambda: db.table("reviews").update(update_dict).eq("id", review_id).execute()
            )

            if not result.data:
                return ResponseModel(success=False, message="Failed to update review", data=None)

            review = Review(**result.data[0])
            log.info(f"Review updated: {review_id} by user {user_id}")

            return ResponseModel(
                success=True,
                message="Review updated successfully",
                data=ReviewOperationResponse(review=review, message="Review updated successfully")
            )

        except Exception as e:
            log.error(f"Error updating review: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    async def get_reviews_by_workshop(self, workshop_id: UUID, limit: int = DEFAULT_LIMIT, offset: int = 0, db: Client = None) -> ResponseModel[ReviewListResponse]:
        """Get all reviews for a workshop"""
        try:
            limit, offset = self._validate_pagination(limit, offset)
            
            # Get reviews with user info
            result = await run_in_threadpool(
                lambda: db.table("reviews").select(
                    "*, users(id, name, email, profile_pic_url, created_at, role)"
                ).eq("workshop_id", str(workshop_id))
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1).execute()
            )

            # Get count
            count_result = await run_in_threadpool(
                lambda: db.table("reviews").select("id", count="exact")
                .eq("workshop_id", str(workshop_id)).execute()
            )

            reviews_with_user = []
            total_rating = 0
            rating_count = 0

            for review_data in result.data:
                user_data = review_data.pop('users', None)
                user = User(**user_data) if user_data else None
                
                review_with_user = ReviewWithUser(**review_data, user=user)
                reviews_with_user.append(review_with_user)
                
                if review_data.get('rating'):
                    total_rating += review_data['rating']
                    rating_count += 1

            # Calculate average
            average_rating = round(total_rating / rating_count, 2) if rating_count > 0 else None

            return ResponseModel(
                success=True,
                message="Reviews retrieved successfully",
                data=ReviewListResponse(
                    reviews=reviews_with_user,
                    total_count=count_result.count,
                    workshop_id=workshop_id,
                    average_rating=average_rating
                )
            )

        except Exception as e:
            log.error(f"Error getting workshop reviews: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    async def get_reviews_by_user(self, user_id: UUID, limit: int = DEFAULT_LIMIT, offset: int = 0, db: Client = None) -> ResponseModel[ReviewListResponse]:
        """Get all reviews by a user"""
        try:
            limit, offset = self._validate_pagination(limit, offset)
            
            result = await run_in_threadpool(
                lambda: db.table("reviews").select(
                    "*, users(id, name, email, profile_pic_url, created_at, role)"
                ).eq("user_id", str(user_id))
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1).execute()
            )

            count_result = await run_in_threadpool(
                lambda: db.table("reviews").select("id", count="exact")
                .eq("user_id", str(user_id)).execute()
            )

            reviews_with_user = []
            for review_data in result.data:
                user_data = review_data.pop('users', None)
                user = User(**user_data) if user_data else None
                review_with_user = ReviewWithUser(**review_data, user=user)
                reviews_with_user.append(review_with_user)

            return ResponseModel(
                success=True,
                message="User reviews retrieved successfully",
                data=ReviewListResponse(
                    reviews=reviews_with_user,
                    total_count=count_result.count,
                    workshop_id=None,
                    average_rating=None
                )
            )

        except Exception as e:
            log.error(f"Error getting user reviews: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    async def get_average_rating(self, workshop_id: UUID, db: Client) -> ResponseModel[Dict]:
        """Get workshop rating statistics"""
        try:
            result = await run_in_threadpool(
                lambda: db.table("reviews").select("rating")
                .eq("workshop_id", str(workshop_id)).execute()
            )

            if not result.data:
                return ResponseModel(
                    success=True,
                    message="No reviews found",
                    data={
                        "workshop_id": workshop_id,
                        "average_rating": 0.0,
                        "total_reviews": 0,
                        "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                    }
                )

            ratings = [r["rating"] for r in result.data if r["rating"]]
            
            if not ratings:
                return ResponseModel(success=True, message="No valid ratings", data={
                    "workshop_id": workshop_id, "average_rating": 0.0, "total_reviews": 0,
                    "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                })

            # Calculate stats
            average_rating = sum(ratings) / len(ratings)
            rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for rating in ratings:
                rating_distribution[rating] += 1

            return ResponseModel(
                success=True,
                message="Rating statistics retrieved",
                data={
                    "workshop_id": workshop_id,
                    "average_rating": round(average_rating, 2),
                    "total_reviews": len(ratings),
                    "rating_distribution": rating_distribution
                }
            )

        except Exception as e:
            log.error(f"Error getting average rating: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    async def delete_review(self, review_id: int, user_id: UUID, is_admin: bool, db: Client) -> ResponseModel[Dict]:
        """Delete a review"""
        try:
            # Check permission
            if is_admin:
                existing = await run_in_threadpool(
                    lambda: db.table("reviews").select("*").eq("id", review_id).execute()
                )
            else:
                existing = await run_in_threadpool(
                    lambda: db.table("reviews").select("*").eq("id", review_id)
                    .eq("user_id", str(user_id)).execute()
                )

            if not existing.data:
                return ResponseModel(success=False, message="Review not found or access denied", data=None)

            # Delete
            result = await run_in_threadpool(
                lambda: db.table("reviews").delete().eq("id", review_id).execute()
            )

            if not result.data:
                return ResponseModel(success=False, message="Failed to delete review", data=None)

            log.info(f"Review deleted: {review_id} by user {user_id} (admin: {is_admin})")
            return ResponseModel(
                success=True,
                message="Review deleted successfully",
                data={"deleted_review_id": review_id}
            )

        except Exception as e:
            log.error(f"Error deleting review: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

# Singleton instance
review_service = ReviewService()
