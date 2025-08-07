"""
Notification Router for Workshop Email Reminders
Simple external service endpoints for automated email reminders
"""

from fastapi import APIRouter, HTTPException, status
import logging

from app.services.notification import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])
logger = logging.getLogger(__name__)

# External Service Endpoints - No Authentication Required
@router.post("/send-1day-reminders")
def send_1day_reminders():
    """
    Check and send 1-day reminder emails for workshops starting tomorrow
    Called by external service - checks if <=1 day left and reminder not sent
    """
    try:
        logger.info("External service: 1-day reminders check started")
        
        result = NotificationService.send_1day_reminders()
        
        return {
            "success": True,
            "message": result.get("message", "Processing completed"),
            "count": result.get("count", 0),
            "total_found": result.get("total_found", 0),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        logger.error(f"Error in 1-day reminders: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "total_found": 0,
            "errors": []
        }

@router.post("/send-15min-reminders")
def send_15min_reminders():
    """
    Check and send 15-minute reminder emails for workshops starting soon
    Called by external service - checks if <=15 min left and reminder not sent
    """
    try:
        logger.info("External service: 15-min reminders check started")
        
        result = NotificationService.send_15min_reminders()
        
        return {
            "success": True,
            "message": result.get("message", "Processing completed"),
            "count": result.get("count", 0),
            "total_found": result.get("total_found", 0),
            "errors": result.get("errors", [])
        }
        
    except Exception as e:
        logger.error(f"Error in 15-min reminders: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "total_found": 0,
            "errors": []
        }

@router.get("/stats")
def get_notification_stats():
    """
    Get notification statistics
    Called by external service to check email status
    """
    try:
        logger.info("External service: Stats requested")
        
        stats = NotificationService.get_notification_stats()
        
        return {
            "success": True,
            "data": stats,
            "message": "Statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
