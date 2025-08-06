# app/routers/assignments.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from uuid import UUID
from typing import Optional

from app.core.logger import setup_logger
from app.services.assignment import AssignmentService
from app.services.user import UserService
from app.schemas.assignment import (
    AssignmentSubmit, AssignmentGrade, AssignmentResponse, 
    AssignmentListResponse, AssignmentStatus
)
from app.schemas.response import ResponseModel
from app.schemas.user import User
from app.dependencies.auth import verify_valid_token, require_admin
from app.dependencies.user_workshop import get_current_registered_user

log = setup_logger(__name__)
router = APIRouter(prefix="/assignments", tags=["Assignments"])

# 📝 Route 1: Submit Assignment (Student)
@router.put("/submit/{workshop_id}", response_model=ResponseModel[AssignmentResponse])
async def submit_assignment(
    workshop_id: UUID,
    assignment_data: AssignmentSubmit,
    current_user: User = Depends(get_current_registered_user)
):
    """
    Submit assignment for a workshop
    - Requires authentication
    - User must be enrolled in workshop
    - Updates existing assignment with submission data
    - Awards 20 points for first-time submission
    """
    try:
        log.info(f"User {current_user.email} submitting assignment for workshop {workshop_id}")
        
        # Check if assignment is already submitted (to determine if points should be awarded)
        existing_assignment = await AssignmentService.get_assignment_for_user_in_workshop(
            current_user.id, workshop_id
        )
        
        is_first_submission = False
        if existing_assignment.success:
            assignment = existing_assignment.data.assignment
            # Check if assignment was in PENDING status (first-time submission)
            if assignment.status == AssignmentStatus.PENDING:
                is_first_submission = True
        
        # Submit the assignment
        result = await AssignmentService.submit_assignment(
            current_user.id, 
            workshop_id, 
            assignment_data
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        # Award points for first-time submission
        points_awarded = 0
        if is_first_submission:
            try:
                points_result = UserService.increment_user_points(current_user.id, 20)
                if points_result.success:
                    points_awarded = 20
                    log.info(f"20 points awarded to user {current_user.id} for assignment submission")
                else:
                    log.warning(f"Failed to award points to user {current_user.id}: {points_result.message}")
            except Exception as e:
                log.error(f"Error awarding points to user {current_user.id}: {str(e)}")
        
        log.info(f"Assignment submitted successfully by user {current_user.id}")
        
        # Update response message to include points info
        response_data = result.data
        if points_awarded > 0:
            response_data.message = f"Assignment submitted successfully! You earned {points_awarded} points!"
        else:
            response_data.message = "Assignment updated successfully!"
        
        return ResponseModel(
            success=True,
            message=response_data.message,
            data=response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error submitting assignment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit assignment"
        )

# 🎯 Route 2: Grade Assignment (Admin Only)
@router.patch("/grade/{assignment_id}", response_model=ResponseModel[AssignmentResponse])
async def grade_assignment(
    assignment_id: int,
    grade_data: AssignmentGrade,
    _: str = Depends(require_admin)
):
    """
    Grade assignment with feedback and marks
    - Admin access required
    - Updates assignment status, feedback, and marks
    - Awards points equal to marks given (if marks provided)
    """
    try:
        log.info(f"Admin grading assignment {assignment_id}")
        
        result = await AssignmentService.grade_assignment(assignment_id, grade_data)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        # Award points equal to marks given (if marks provided)
        points_awarded = 0
        if grade_data.marks is not None and grade_data.marks > 0:
            try:
                # Get the assignment to find the user_id
                assignment = result.data.assignment
                points_result = UserService.increment_user_points(assignment.user_id, grade_data.marks)
                if points_result.success:
                    points_awarded = grade_data.marks
                    log.info(f"{points_awarded} points awarded to user {assignment.user_id} for assignment grade")
                else:
                    log.warning(f"Failed to award points to user {assignment.user_id}: {points_result.message}")
            except Exception as e:
                log.error(f"Error awarding points for assignment grade: {str(e)}")
        
        log.info(f"Assignment {assignment_id} graded successfully")
        
        # Update response message to include points info
        response_data = result.data
        if points_awarded > 0:
            response_data.message = f"Assignment graded successfully! User awarded {points_awarded} points for their marks!"
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error grading assignment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grade assignment"
        )

# 📋 Route 3: Get Assignment Details
@router.get("/{assignment_id}", response_model=ResponseModel[AssignmentResponse])
async def get_assignment_details(
    assignment_id: int,
    _: str = Depends(verify_valid_token)
):
    """
    Get assignment details by ID
    - Requires authentication
    - Returns complete assignment information
    """
    try:
        log.debug(f"Fetching assignment details for ID: {assignment_id}")
        
        result = await AssignmentService.get_assignment_by_id(assignment_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching assignment details")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch assignment details"
        )

# 👤 Route 4: Get My Assignments
@router.get("/user/my-assignments", response_model=ResponseModel[AssignmentListResponse])
async def get_my_assignments(
    current_user: User = Depends(get_current_registered_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get current user's assignments
    - Requires authentication
    - Returns paginated list of user's assignments
    """
    try:
        log.debug(f"Fetching assignments for user: {current_user.email}")
        
        result = await AssignmentService.get_assignments_by_user(
            current_user.id, limit, offset
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching user assignments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch your assignments"
        )

# 🏢 Route 5: Get Workshop Assignments (Admin)
@router.get("/workshop/{workshop_id}", response_model=ResponseModel[AssignmentListResponse])
async def get_workshop_assignments(
    workshop_id: UUID,
    _: str = Depends(require_admin),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all assignments for a workshop
    - Admin access required
    - Returns paginated list of workshop assignments
    """
    try:
        log.debug(f"Admin fetching assignments for workshop: {workshop_id}")
        
        result = await AssignmentService.get_assignments_by_workshop(
            workshop_id, limit, offset
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching workshop assignments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch workshop assignments"
        )

# 🔍 Route 6: Get User's Assignment for Specific Workshop
@router.get("/user/{user_id}/workshop/{workshop_id}", response_model=ResponseModel[AssignmentResponse])
async def get_user_workshop_assignment(
    user_id: UUID,
    workshop_id: UUID,
    current_user: User = Depends(get_current_registered_user)
):
    """
    Get user's assignment for specific workshop
    - Users can only view their own assignments
    - Admins can view any user's assignment
    """
    try:
        # Check if user is requesting their own assignment or is admin
        if current_user.id != user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own assignments"
            )
        
        log.debug(f"Fetching assignment for user {user_id} in workshop {workshop_id}")
        
        result = await AssignmentService.get_assignment_for_user_in_workshop(
            user_id, workshop_id
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error fetching user workshop assignment")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch assignment"
        )

# 📊 Route 7: List All Assignments with Filters (Admin)
@router.get("/", response_model=ResponseModel[AssignmentListResponse])
async def list_assignments(
    _: str = Depends(require_admin),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[AssignmentStatus] = Query(None),
    workshop_id: Optional[UUID] = Query(None),
    user_id: Optional[UUID] = Query(None)
):
    """
    List all assignments with optional filters
    - Admin access required
    - Supports filtering by status, workshop_id, user_id
    - Returns paginated results
    """
    try:
        log.debug(f"Admin listing assignments with filters")
        
        result = await AssignmentService.list_assignments_paginated(
            limit=limit,
            offset=offset,
            status=status,
            workshop_id=workshop_id,
            user_id=user_id
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log.exception(f"Error listing assignments")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list assignments"
        )
