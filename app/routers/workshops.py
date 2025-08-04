# app/routers/workshops.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.services.workshop import WorkshopService
from app.schemas.response import ResponseModel
from app.schemas.workshop import (
    WorkshopCreate,
    WorkshopUpdate,
    WorkshopOut,
    WorkshopFilters,
    WorkshopStats
)
from app.dependencies.auth import require_admin, verify_valid_token
from app.core.logger import setup_logger
from typing import List, Dict, Any
from uuid import UUID

router = APIRouter(prefix="/workshops", tags=["Workshops"])
log = setup_logger(__name__)

# 🔹 1. Create Workshop (Admin only)
@router.post("/", response_model=ResponseModel[WorkshopOut])
async def create_workshop(
    payload: WorkshopCreate,
    user: dict = Depends(require_admin)
):
    """
    Create a new workshop (Admin only)
    
    Required fields:
    - title: Workshop title (3-200 chars)
    - conducted_by: Instructor name
    - scheduled_at: Future datetime in IST
    - Optional: description, technologies
    """
    try:
        log.info(f"Admin creating workshop: {payload.title}")
        workshop = WorkshopService.create_workshop(payload)  # Sync call, no await
        return ResponseModel(
            message="Workshop created successfully", 
            data=workshop
        )
    except Exception as e:
        log.error(f"Failed to create workshop: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create workshop: {str(e)}"
        )

# 🔹 2. Get Workshop Statistics (Put BEFORE /{workshop_id})
@router.get("/stats", response_model=ResponseModel[WorkshopStats])
async def get_workshop_stats():
    """
    Get workshop statistics
    
    Returns:
    - Total workshops count
    - Upcoming vs past workshops
    - Popular technologies
    - Active instructors count
    - Next upcoming workshop
    """
    try:
        stats = WorkshopService.get_workshop_stats()  # Sync call
        return ResponseModel(
            message="Workshop statistics fetched successfully", 
            data=stats
        )
    except Exception as e:
        log.error(f"Failed to get workshop stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch statistics: {str(e)}"
        )

# 🔹 3. Get Upcoming Workshops
@router.get("/upcoming", response_model=ResponseModel[List[WorkshopOut]])
async def get_upcoming_workshops(
    limit: int = Query(default=10, ge=1, le=50, description="Number of workshops to fetch")
):
    """Get upcoming workshops ordered by date"""
    try:
        workshops = WorkshopService.get_upcoming_workshops(limit=limit)
        return ResponseModel(
            message=f"Fetched {len(workshops)} upcoming workshops", 
            data=workshops
        )
    except Exception as e:
        log.error(f"Failed to get upcoming workshops: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch upcoming workshops: {str(e)}"
        )

# 🔹 4. Search Workshops by Technology
@router.get("/technology/{tech_name}", response_model=ResponseModel[List[WorkshopOut]])
async def search_by_technology(
    tech_name: str,
    user: dict = Depends(verify_valid_token)  # Any logged in user can search
):
    """Search workshops by specific technology"""
    try:
        workshops = WorkshopService.search_workshops_by_technology(tech_name)
        return ResponseModel(
            message=f"Found {len(workshops)} workshops for technology: {tech_name}", 
            data=workshops
        )
    except Exception as e:
        log.error(f"Failed to search workshops by technology '{tech_name}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search workshops: {str(e)}"
        )

# 🔹 5. Get All Workshops with Filters
@router.get("/", response_model=ResponseModel[Dict[str, Any]])
async def get_all_workshops(
    search: str = Query(None, description="Search in title and description"),
    technology: str = Query(None, description="Filter by technology"),
    instructor: str = Query(None, description="Filter by instructor name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Get all workshops with advanced filtering and pagination
    
    Query Parameters:
    - search: Search text in title/description
    - technology: Filter by specific technology
    - instructor: Filter by instructor name
    - page: Page number (default: 1)
    - page_size: Items per page (default: 20, max: 100)
    """
    try:
        filters = WorkshopFilters(
            search=search,
            technology=technology,
            instructor=instructor,
            page=page,
            page_size=page_size
        )
        
        result = WorkshopService.list_workshops(filters)
        return ResponseModel(
            message=f"Fetched {len(result['workshops'])} workshops", 
            data=result
        )
    except Exception as e:
        log.error(f"Failed to get workshops: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch workshops: {str(e)}"
        )

# 🔹 6. Get Workshop by ID (Put AFTER other GET routes)
@router.get("/{workshop_id}", response_model=ResponseModel[WorkshopOut])
async def get_workshop_by_id(
    workshop_id: UUID
):
    """
    Get workshop by ID
    
    Returns detailed workshop information including:
    - All workshop details
    - Computed fields (is_upcoming, time_until_workshop)
    - IST formatted dates
    """
    try:
        workshop = WorkshopService.get_workshop_by_id(workshop_id)
        return ResponseModel(
            message="Workshop details fetched successfully", 
            data=workshop
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions from service
    except Exception as e:
        log.error(f"Failed to get workshop {workshop_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch workshop: {str(e)}"
        )

# 🔹 7. Update Workshop (Admin only)
@router.patch("/{workshop_id}", response_model=ResponseModel[WorkshopOut])
async def update_workshop(
    workshop_id: UUID,
    payload: WorkshopUpdate,
    user: dict = Depends(require_admin)
):
    """
    Update workshop (Admin only)
    
    Updatable fields:
    - title, description, technologies
    - conducted_by, scheduled_at
    
    Note: Computed fields (is_upcoming, time_until_workshop, scheduled_at_ist) 
    are automatically recalculated and should NOT be included in update payload.
    Only non-null fields will be updated.
    """
    try:
        log.debug(f"Admin updating workshop: {workshop_id}")
        workshop = WorkshopService.update_workshop(workshop_id, payload)
        return ResponseModel(
            message="Workshop updated successfully", 
            data=workshop
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions from service
    except Exception as e:
        log.error(f"Failed to update workshop {workshop_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update workshop: {str(e)}"
        )

# 🔹 8. Delete Workshop (Admin only)
@router.delete("/{workshop_id}", response_model=ResponseModel[Dict[str, str]])
async def delete_workshop(
    workshop_id: UUID,
    user: dict = Depends(require_admin)
):
    """
    Delete workshop (Admin only)
    
    Permanently removes workshop from database.
    This action cannot be undone.
    """
    try:
        log.info(f"Admin deleting workshop: {workshop_id}")
        result = WorkshopService.delete_workshop(workshop_id)
        return ResponseModel(
            message="Workshop deleted successfully", 
            data=result
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions from service
    except Exception as e:
        log.error(f"Failed to delete workshop {workshop_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete workshop: {str(e)}"
        )