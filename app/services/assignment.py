# app/services/assignment.py
from app.core.logger import setup_logger
from app.core.db import get_db
from app.schemas.assignment import (
    Assignment, AssignmentAutoCreate, AssignmentSubmit, AssignmentGrade,
    AssignmentResponse, AssignmentListResponse, AssignmentStats,
    AssignmentStatus
)
from app.schemas.response import ResponseModel
from uuid import UUID
from typing import List, Optional, Dict, Any
from fastapi.concurrency import run_in_threadpool
from supabase import Client

log = setup_logger(__name__)

# Constants
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

class AssignmentService:
    
    @staticmethod
    def _validate_pagination(limit: int, offset: int) -> tuple[int, int]:
        """Validate pagination parameters"""
        limit = max(1, min(limit, MAX_LIMIT))
        offset = max(0, offset)
        return limit, offset

    @staticmethod
    async def create_assignment_on_enroll(user_id: UUID, workshop_id: UUID) -> bool:
        """Simple assignment creation when user enrolls in workshop"""
        try:
            db = get_db()
            
            # Check if assignment already exists
            existing = await run_in_threadpool(
                lambda: db.table("assignments").select("id")
                .eq("user_id", str(user_id))
                .eq("workshop_id", str(workshop_id)).execute()
            )

            if existing.data:
                log.info(f"Assignment already exists for user {user_id} in workshop {workshop_id}")
                return True

            # Create simple assignment
            assignment_data = {
                "user_id": str(user_id),
                "workshop_id": str(workshop_id),
                "status": AssignmentStatus.PENDING.value
            }

            result = await run_in_threadpool(
                lambda: db.table("assignments").insert(assignment_data).execute()
            )

            if result.data:
                log.info(f"Assignment created for user {user_id} in workshop {workshop_id}")
                return True
            else:
                log.error(f"Failed to create assignment for user {user_id} in workshop {workshop_id}")
                return False

        except Exception as e:
            log.error(f"Error creating assignment: {str(e)}")
            return False

    @staticmethod
    async def submit_assignment(user_id: UUID, workshop_id: UUID, assignment_data: AssignmentSubmit) -> ResponseModel[AssignmentResponse]:
        """User submits their assignment"""
        try:
            db = get_db()
            
            # Find user's assignment for this workshop
            existing = await run_in_threadpool(
                lambda: db.table("assignments").select("*")
                .eq("user_id", str(user_id))
                .eq("workshop_id", str(workshop_id)).execute()
            )

            if not existing.data:
                return ResponseModel(
                    success=False,
                    message="No assignment found for this workshop",
                    data=None
                )

            assignment_id = existing.data[0]["id"]

            # Update assignment with submission data
            update_data = {
                "title": assignment_data.title,
                "submit_link": assignment_data.submit_link,
                "status": AssignmentStatus.SUBMITTED.value
            }

            result = await run_in_threadpool(
                lambda: db.table("assignments").update(update_data)
                .eq("id", assignment_id).execute()
            )

            if not result.data:
                return ResponseModel(success=False, message="Failed to submit assignment", data=None)

            assignment = Assignment(**result.data[0])
            log.info(f"Assignment submitted: {assignment_id} by user {user_id}")

            return ResponseModel(
                success=True,
                message="Assignment submitted successfully",
                data=AssignmentResponse(
                    assignment=assignment,
                    message="Assignment submitted and ready for review",
                    success=True
                )
            )

        except Exception as e:
            log.error(f"Error submitting assignment: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    @staticmethod
    async def grade_assignment(assignment_id: int, grade_data: AssignmentGrade) -> ResponseModel[AssignmentResponse]:
        """Admin grades assignment with feedback and marks"""
        try:
            db = get_db()
            
            # Check if assignment exists
            existing = await run_in_threadpool(
                lambda: db.table("assignments").select("*").eq("id", assignment_id).execute()
            )

            if not existing.data:
                return ResponseModel(
                    success=False,
                    message="Assignment not found",
                    data=None
                )

            # Update assignment with grading data
            update_data = {
                "status": grade_data.status.value,
                "feedback": grade_data.feedback,
                "marks": grade_data.marks
            }

            result = await run_in_threadpool(
                lambda: db.table("assignments").update(update_data)
                .eq("id", assignment_id).execute()
            )

            if not result.data:
                return ResponseModel(success=False, message="Failed to grade assignment", data=None)

            assignment = Assignment(**result.data[0])
            log.info(f"Assignment graded: {assignment_id} with status {grade_data.status}")

            return ResponseModel(
                success=True,
                message="Assignment graded successfully",
                data=AssignmentResponse(
                    assignment=assignment,
                    message=f"Assignment {grade_data.status.value} with marks: {grade_data.marks or 'N/A'}",
                    success=True
                )
            )

        except Exception as e:
            log.error(f"Error grading assignment: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    @staticmethod
    async def get_assignment_by_id(assignment_id: int) -> ResponseModel[AssignmentResponse]:
        """Get specific assignment by ID"""
        try:
            db = get_db()
            
            result = await run_in_threadpool(
                lambda: db.table("assignments").select("*").eq("id", assignment_id).execute()
            )

            if not result.data:
                return ResponseModel(
                    success=False,
                    message="Assignment not found",
                    data=None
                )

            assignment = Assignment(**result.data[0])

            return ResponseModel(
                success=True,
                message="Assignment retrieved successfully",
                data=AssignmentResponse(
                    assignment=assignment,
                    message="Assignment details",
                    success=True
                )
            )

        except Exception as e:
            log.error(f"Error getting assignment: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    @staticmethod
    async def get_assignments_by_user(user_id: UUID, limit: int = DEFAULT_LIMIT, offset: int = 0) -> ResponseModel[AssignmentListResponse]:
        """Get all assignments for a user"""
        try:
            db = get_db()
            limit, offset = AssignmentService._validate_pagination(limit, offset)

            result = await run_in_threadpool(
                lambda: db.table("assignments").select("*")
                .eq("user_id", str(user_id))
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1).execute()
            )

            count_result = await run_in_threadpool(
                lambda: db.table("assignments").select("id", count="exact")
                .eq("user_id", str(user_id)).execute()
            )

            assignments = [Assignment(**assignment_data) for assignment_data in result.data]

            return ResponseModel(
                success=True,
                message="User assignments retrieved successfully",
                data=AssignmentListResponse(
                    assignments=assignments,
                    total_count=count_result.count,
                    user_id=user_id,
                    page=offset // limit + 1,
                    per_page=limit,
                    has_next=count_result.count > offset + limit
                )
            )

        except Exception as e:
            log.error(f"Error getting user assignments: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    @staticmethod
    async def get_assignments_by_workshop(workshop_id: UUID, limit: int = DEFAULT_LIMIT, offset: int = 0) -> ResponseModel[AssignmentListResponse]:
        """Get all assignments for a workshop"""
        try:
            db = get_db()
            limit, offset = AssignmentService._validate_pagination(limit, offset)

            result = await run_in_threadpool(
                lambda: db.table("assignments").select("*")
                .eq("workshop_id", str(workshop_id))
                .order("created_at", desc=True)
                .range(offset, offset + limit - 1).execute()
            )

            count_result = await run_in_threadpool(
                lambda: db.table("assignments").select("id", count="exact")
                .eq("workshop_id", str(workshop_id)).execute()
            )

            assignments = [Assignment(**assignment_data) for assignment_data in result.data]

            return ResponseModel(
                success=True,
                message="Workshop assignments retrieved successfully",
                data=AssignmentListResponse(
                    assignments=assignments,
                    total_count=count_result.count,
                    workshop_id=workshop_id,
                    page=offset // limit + 1,
                    per_page=limit,
                    has_next=count_result.count > offset + limit
                )
            )

        except Exception as e:
            log.error(f"Error getting workshop assignments: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    @staticmethod
    async def get_assignment_for_user_in_workshop(user_id: UUID, workshop_id: UUID) -> ResponseModel[AssignmentResponse]:
        """Get user's assignment for specific workshop"""
        try:
            db = get_db()
            
            result = await run_in_threadpool(
                lambda: db.table("assignments").select("*")
                .eq("user_id", str(user_id))
                .eq("workshop_id", str(workshop_id)).execute()
            )

            if not result.data:
                return ResponseModel(
                    success=False,
                    message="No assignment found for this user in this workshop",
                    data=None
                )

            assignment = Assignment(**result.data[0])

            return ResponseModel(
                success=True,
                message="Assignment retrieved successfully",
                data=AssignmentResponse(
                    assignment=assignment,
                    message="User's workshop assignment",
                    success=True
                )
            )

        except Exception as e:
            log.error(f"Error getting user workshop assignment: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)

    @staticmethod
    async def list_assignments_paginated(limit: int = DEFAULT_LIMIT, offset: int = 0, status: Optional[AssignmentStatus] = None, workshop_id: Optional[UUID] = None, user_id: Optional[UUID] = None) -> ResponseModel[AssignmentListResponse]:
        """Get paginated list of assignments with optional filters"""
        try:
            db = get_db()
            limit, offset = AssignmentService._validate_pagination(limit, offset)

            # Build query
            query = db.table("assignments").select("*")
            count_query = db.table("assignments").select("id", count="exact")

            # Apply filters
            if status:
                query = query.eq("status", status.value)
                count_query = count_query.eq("status", status.value)
            
            if workshop_id:
                query = query.eq("workshop_id", str(workshop_id))
                count_query = count_query.eq("workshop_id", str(workshop_id))
            
            if user_id:
                query = query.eq("user_id", str(user_id))
                count_query = count_query.eq("user_id", str(user_id))

            # Execute queries
            result = await run_in_threadpool(
                lambda: query.order("created_at", desc=True)
                .range(offset, offset + limit - 1).execute()
            )

            count_result = await run_in_threadpool(lambda: count_query.execute())

            assignments = [Assignment(**assignment_data) for assignment_data in result.data]

            return ResponseModel(
                success=True,
                message="Assignments retrieved successfully",
                data=AssignmentListResponse(
                    assignments=assignments,
                    total_count=count_result.count,
                    workshop_id=workshop_id,
                    user_id=user_id,
                    page=offset // limit + 1,
                    per_page=limit,
                    has_next=count_result.count > offset + limit
                )
            )

        except Exception as e:
            log.error(f"Error listing assignments: {str(e)}")
            return ResponseModel(success=False, message=str(e), data=None)
