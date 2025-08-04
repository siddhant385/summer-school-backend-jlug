# app/services/workshop.py
from uuid import UUID
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from app.core.db import get_db, get_db_admin
from app.schemas.workshop import WorkshopCreate, WorkshopUpdate, WorkshopOut, WorkshopFilters, WorkshopStats
from app.core.logger import setup_logger
from datetime import datetime
from zoneinfo import ZoneInfo

log = setup_logger(__name__)
IST = ZoneInfo("Asia/Kolkata")

class WorkshopService:

    @staticmethod
    def create_workshop(data: WorkshopCreate) -> WorkshopOut:
        """Create a new workshop with proper validation"""
        db = get_db_admin()  # Use admin DB for write operations
        try:
            # Convert datetime to proper format for database
            insert_data = data.model_dump()
            
            # Ensure datetime is properly formatted for Supabase
            if isinstance(insert_data['scheduled_at'], datetime):
                insert_data['scheduled_at'] = insert_data['scheduled_at'].isoformat()
            
            log.debug(f"Creating workshop: {insert_data['title']}")
            
            response = db.table("workshops").insert(insert_data).execute()
            
            if not response.data:
                log.error("Failed to create workshop - no data returned")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                    detail="Failed to create workshop"
                )
            
            created_workshop = response.data[0]
            log.info(f"Workshop created: {created_workshop['title']} (ID: {created_workshop['id']})")
            
            return WorkshopOut(**created_workshop)
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error creating workshop: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Internal server error: {str(e)}"
            )

    @staticmethod
    def get_workshop_by_id(workshop_id: UUID) -> WorkshopOut:
        """Get workshop by ID with error handling"""
        db = get_db()
        try:
            log.debug(f"Fetching workshop: {workshop_id}")
            
            response = db.table("workshops").select("*").eq("id", str(workshop_id)).execute()
            
            if not response.data or len(response.data) == 0:
                log.warning(f"Workshop not found: {workshop_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, 
                    detail=f"Workshop with ID {workshop_id} not found"
                )
            
            workshop_data = response.data[0]
            log.debug(f"Workshop fetched: {workshop_data['title']}")
            
            return WorkshopOut(**workshop_data)
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error fetching workshop {workshop_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error fetching workshop: {str(e)}"
            )

    @staticmethod
    def update_workshop(workshop_id: UUID, data: WorkshopUpdate) -> WorkshopOut:
        """Update workshop with validation"""
        db = get_db_admin()  # Use admin DB for write operations
        try:
            log.debug(f"Updating workshop: {workshop_id}")
            
            # Check if workshop exists first
            existing_response = db.table("workshops").select("*").eq("id", str(workshop_id)).execute()
            if not existing_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workshop with ID {workshop_id} not found"
                )
            
            # Prepare update data (only include non-None values)
            update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
            
            if not update_data:
                log.debug("No data provided for update")
                return WorkshopOut(**existing_response.data[0])
            
            # Convert datetime to proper format
            if 'scheduled_at' in update_data and isinstance(update_data['scheduled_at'], datetime):
                update_data['scheduled_at'] = update_data['scheduled_at'].isoformat()
            
            response = db.table("workshops").update(update_data).eq("id", str(workshop_id)).execute()
            
            if not response.data:
                log.error(f"Failed to update workshop: {workshop_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Update operation failed"
                )
            
            updated_workshop = response.data[0]
            log.info(f"Workshop updated: {updated_workshop['title']}")
            
            return WorkshopOut(**updated_workshop)
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error updating workshop {workshop_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error updating workshop: {str(e)}"
            )

    @staticmethod
    def delete_workshop(workshop_id: UUID) -> Dict[str, str]:
        """Delete workshop with validation"""
        db = get_db_admin()  # Use admin DB for write operations
        try:
            log.debug(f"Deleting workshop: {workshop_id}")
            
            # Check if workshop exists first
            existing_response = db.table("workshops").select("*").eq("id", str(workshop_id)).execute()
            if not existing_response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workshop with ID {workshop_id} not found"
                )
            
            workshop_title = existing_response.data[0]['title']
            
            response = db.table("workshops").delete().eq("id", str(workshop_id)).execute()
            
            if not response.data:
                log.error(f"Failed to delete workshop: {workshop_id}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Delete operation failed"
                )
            
            log.info(f"Workshop deleted: {workshop_title}")
            return {
                "message": "Workshop deleted successfully", 
                "deleted_workshop": workshop_title,
                "deleted_id": str(workshop_id)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error deleting workshop {workshop_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error deleting workshop: {str(e)}"
            )

    # app/services/workshop.py
    # Fix the list_workshops method
    @staticmethod
    def list_workshops(filters: WorkshopFilters) -> Dict[str, Any]:
        """List workshops with advanced filtering and pagination"""
        db = get_db()
        try:
            log.debug(f"Listing workshops with filters: page={filters.page}, search='{filters.search}'")
            
            # Start with base query
            query = db.table("workshops").select("*")

            # Apply filters
            if filters.search:
                # Search in both title and description
                query = query.or_(f"title.ilike.%{filters.search}%,description.ilike.%{filters.search}%")

            if filters.technology:
                # Check if technology exists in the technologies array
                query = query.contains("technologies", [filters.technology])

            if filters.instructor:
                query = query.ilike("conducted_by", f"%{filters.instructor}%")

            if filters.from_date:
                query = query.gte("scheduled_at", filters.from_date.isoformat())

            if filters.to_date:
                query = query.lte("scheduled_at", filters.to_date.isoformat())

            # 🔧 Fix: Get total count properly
            try:
                # First get count using head() method
                count_query = db.table("workshops").select("id")
                
                # Apply same filters to count query
                if filters.search:
                    count_query = count_query.or_(f"title.ilike.%{filters.search}%,description.ilike.%{filters.search}%")
                if filters.technology:
                    count_query = count_query.contains("technologies", [filters.technology])
                if filters.instructor:
                    count_query = count_query.ilike("conducted_by", f"%{filters.instructor}%")
                if filters.from_date:
                    count_query = count_query.gte("scheduled_at", filters.from_date.isoformat())
                if filters.to_date:
                    count_query = count_query.lte("scheduled_at", filters.to_date.isoformat())
                
                # Use head() with count to get total count
                count_response = count_query.execute()
                total = len(count_response.data or [])
                
            except Exception as count_error:
                log.warning(f"Count query failed: {count_error}, using fallback method")
                # Fallback: get all data and count manually
                try:
                    fallback_response = db.table("workshops").select("id").execute()
                    total = len(fallback_response.data or [])
                except:
                    total = 0

            # Apply pagination and ordering
            start_range = (filters.page - 1) * filters.page_size
            end_range = start_range + filters.page_size - 1
            
            response = (
                query
                .order("scheduled_at", desc=False)
                .range(start_range, end_range)
                .execute()
            )

            workshops_data = response.data or []
            workshops = [WorkshopOut(**row) for row in workshops_data]
            
            # Calculate pagination info
            has_next = total > filters.page * filters.page_size
            has_prev = filters.page > 1
            total_pages = (total + filters.page_size - 1) // filters.page_size
            
            log.debug(f"Found {len(workshops)} workshops (total: {total})")

            return {
                "workshops": workshops,
                "pagination": {
                    "total": total,
                    "page": filters.page,
                    "page_size": filters.page_size,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev,
                },
                "filters_applied": {
                    "search": filters.search,
                    "technology": filters.technology,
                    "instructor": filters.instructor,
                    "date_range": bool(filters.from_date or filters.to_date)
                }
            }
            
        except Exception as e:
            log.error(f"Error listing workshops: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Error fetching workshops: {str(e)}"
            )

    @staticmethod
    def get_upcoming_workshops(limit: int = 10) -> List[WorkshopOut]:
        """Get upcoming workshops ordered by date"""
        db = get_db()
        try:
            current_time = datetime.now(IST).isoformat()
            
            response = (
                db.table("workshops")
                .select("*")
                .gte("scheduled_at", current_time)
                .order("scheduled_at", desc=False)
                .limit(limit)
                .execute()
            )
            
            workshops_data = response.data or []
            return [WorkshopOut(**row) for row in workshops_data]
            
        except Exception as e:
            log.error(f"Error fetching upcoming workshops: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching upcoming workshops: {str(e)}"
            )

    @staticmethod
    def get_workshop_stats() -> WorkshopStats:
        """Get workshop statistics"""
        db = get_db()
        try:
            log.debug("Generating workshop statistics")
            
            # Get all workshops
            response = db.table("workshops").select("*").execute()
            workshops = response.data or []
            
            current_time = datetime.now(IST)
            
            # Calculate stats
            total_workshops = len(workshops)
            upcoming_workshops = len([
                w for w in workshops 
                if datetime.fromisoformat(w['scheduled_at'].replace('Z', '+00:00')).astimezone(IST) > current_time
            ])
            past_workshops = total_workshops - upcoming_workshops
            
            # Count technologies
            tech_counter = {}
            for workshop in workshops:
                for tech in workshop.get('technologies', []):
                    tech_counter[tech] = tech_counter.get(tech, 0) + 1
            
            popular_technologies = [
                {"tech": tech, "count": count} 
                for tech, count in sorted(tech_counter.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Count active instructors
            active_instructors = len(set(w['conducted_by'] for w in workshops if w.get('conducted_by')))
            
            # Get next workshop
            next_workshop = None
            upcoming = [
                w for w in workshops 
                if datetime.fromisoformat(w['scheduled_at'].replace('Z', '+00:00')).astimezone(IST) > current_time
            ]
            if upcoming:
                next_workshop_data = min(upcoming, key=lambda x: x['scheduled_at'])
                next_workshop = WorkshopOut(**next_workshop_data)
            
            # Get current IST time for stats
            current_ist_str = current_time.strftime("%d %B %Y, %I:%M %p IST")
            
            stats = WorkshopStats(
                total_workshops=total_workshops,
                upcoming_workshops=upcoming_workshops,
                past_workshops=past_workshops,
                popular_technologies=popular_technologies,
                active_instructors=active_instructors,
                next_workshop=next_workshop,
                current_time_ist=current_ist_str
            )
            
            log.debug(f"Generated stats: {total_workshops} total, {upcoming_workshops} upcoming")
            return stats
            
        except Exception as e:
            log.error(f"Error generating workshop stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating statistics: {str(e)}"
            )

    @staticmethod
    def search_workshops_by_technology(technology: str) -> List[WorkshopOut]:
        """Search workshops by specific technology"""
        db = get_db()
        try:
            response = (
                db.table("workshops")
                .select("*")
                .contains("technologies", [technology])
                .order("scheduled_at", desc=False)
                .execute()
            )
            
            workshops_data = response.data or []
            return [WorkshopOut(**row) for row in workshops_data]
            
        except Exception as e:
            log.error(f"Error searching workshops by technology '{technology}': {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error searching workshops: {str(e)}"
            )