"""
Notification Router for Workshop Email Management
Handles workshop reminder emails and notification status tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel

from app.dependencies.auth import get_current_user, require_admin
from app.services.notification import NotificationService
from app.schemas.response import BaseResponse
import logging

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

# Request/Response Models
class SendWelcomeEmailRequest(BaseModel):
    """Request model for sending welcome email"""
    user_id: UUID
    workshop_id: UUID

class UpdateReminderStatusRequest(BaseModel):
    """Request model for updating reminder status"""
    user_id: UUID
    workshop_id: UUID
    reminder_1day_sent: Optional[bool] = None
    reminder_15min_sent: Optional[bool] = None

class NotificationResponse(BaseModel):
    """Response model for notification operations"""
    success: bool
    message: str
    emails_sent: Optional[int] = None
    failed_emails: Optional[int] = None
    data: Optional[Dict[str, Any]] = None

# Manual Trigger Endpoints (Admin Only)
@router.post("/send-1day-reminders", response_model=BaseResponse)
async def trigger_1day_reminders(
    background_tasks: BackgroundTasks,
    current_user = Depends(require_admin)
):
    """
    Manually trigger 1-day reminder emails for workshops starting tomorrow
    Admin only endpoint for manual execution or testing
    """
    try:
        logger.info(f"1-day reminders triggered manually by admin: {current_user}")
        
        # Run in background to avoid timeout
        background_tasks.add_task(NotificationService.send_1day_reminders)
        
        return BaseResponse(
            success=True,
            message="1-day reminder emails triggered successfully. Processing in background.",
            data={"triggered_by": current_user, "type": "1day_reminders"}
        )
        
    except Exception as e:
        logger.error(f"Error triggering 1-day reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger 1-day reminder emails"
        )

@router.post("/send-15min-reminders", response_model=BaseResponse)
async def trigger_15min_reminders(
    background_tasks: BackgroundTasks,
    current_user = Depends(require_admin)
):
    """
    Manually trigger 15-minute reminder emails for workshops starting soon
    Admin only endpoint for manual execution or testing
    """
    try:
        logger.info(f"15-minute reminders triggered manually by admin: {current_user}")
        
        # Run in background to avoid timeout
        background_tasks.add_task(NotificationService.send_15min_reminders)
        
        return BaseResponse(
            success=True,
            message="15-minute reminder emails triggered successfully. Processing in background.",
            data={"triggered_by": current_user, "type": "15min_reminders"}
        )
        
    except Exception as e:
        logger.error(f"Error triggering 15-minute reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger 15-minute reminder emails"
        )

@router.post("/send-welcome-email", response_model=BaseResponse)
async def send_welcome_email(
    request: SendWelcomeEmailRequest,
    current_user = Depends(get_current_user)
):
    """
    Send workshop welcome email to a specific user
    Can be triggered by user enrollment or admin action
    """
    try:
        logger.info(f"Welcome email requested for user {request.user_id}, workshop {request.workshop_id}")
        
        result = await NotificationService.send_welcome_email(
            user_id=request.user_id,
            workshop_id=request.workshop_id
        )
        
        if result.get("success"):
            return BaseResponse(
                success=True,
                message="Welcome email sent successfully",
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send welcome email: {result.get('error')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending welcome email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send welcome email"
        )

# Status Management Endpoints
@router.post("/update-reminder-status", response_model=BaseResponse)
async def update_reminder_status(
    request: UpdateReminderStatusRequest,
    current_user = Depends(require_admin)
):
    """
    Update reminder status for a specific user-workshop pair
    Admin only endpoint for status management
    """
    try:
        logger.info(f"Reminder status update requested by admin: {current_user}")
        
        result = await NotificationService.update_reminder_status(
            user_id=request.user_id,
            workshop_id=request.workshop_id,
            reminder_1day_sent=request.reminder_1day_sent,
            reminder_15min_sent=request.reminder_15min_sent
        )
        
        return BaseResponse(
            success=True,
            message="Reminder status updated successfully",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating reminder status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update reminder status"
        )

# Monitoring and Analytics Endpoints
@router.get("/stats", response_model=BaseResponse)
async def get_notification_stats(
    current_user = Depends(require_admin)
):
    """
    Get notification statistics and metrics
    Admin only endpoint for monitoring email performance
    """
    try:
        stats = await NotificationService.get_notification_stats()
        
        return BaseResponse(
            success=True,
            message="Notification statistics retrieved successfully",
            data=stats
        )
        
    except Exception as e:
        logger.error(f"Error getting notification stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification statistics"
        )

@router.get("/pending-1day-reminders", response_model=BaseResponse)
async def get_pending_1day_reminders(
    current_user = Depends(require_admin)
):
    """
    Get list of users who need 1-day reminder emails
    Admin only endpoint for monitoring pending notifications
    """
    try:
        pending_reminders = await NotificationService.get_workshops_for_1day_reminder()
        
        # Format response data
        formatted_data = []
        for item in pending_reminders:
            user = item.get("user", {})
            workshop = item.get("workshop", {})
            formatted_data.append({
                "user_id": item.get("user_id"),
                "user_name": user.get("name"),
                "user_email": user.get("email"),
                "workshop_id": item.get("workshop_id"),
                "workshop_title": workshop.get("title"),
                "workshop_start_time": workshop.get("start_time")
            })
        
        return BaseResponse(
            success=True,
            message=f"Found {len(formatted_data)} pending 1-day reminders",
            data={
                "count": len(formatted_data),
                "pending_reminders": formatted_data
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting pending 1-day reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending 1-day reminders"
        )

@router.get("/pending-15min-reminders", response_model=BaseResponse)
async def get_pending_15min_reminders(
    current_user = Depends(require_admin)
):
    """
    Get list of users who need 15-minute reminder emails
    Admin only endpoint for monitoring urgent notifications
    """
    try:
        pending_reminders = await NotificationService.get_workshops_for_15min_reminder()
        
        # Format response data
        formatted_data = []
        for item in pending_reminders:
            user = item.get("user", {})
            workshop = item.get("workshop", {})
            formatted_data.append({
                "user_id": item.get("user_id"),
                "user_name": user.get("name"),
                "user_email": user.get("email"),
                "workshop_id": item.get("workshop_id"),
                "workshop_title": workshop.get("title"),
                "workshop_start_time": workshop.get("start_time"),
                "meeting_link": workshop.get("meeting_link")
            })
        
        return BaseResponse(
            success=True,
            message=f"Found {len(formatted_data)} pending 15-minute reminders",
            data={
                "count": len(formatted_data),
                "pending_reminders": formatted_data
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting pending 15-minute reminders: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending 15-minute reminders"
        )

# Automated Execution Endpoints (for cron jobs/schedulers)
@router.post("/cron/1day-reminders")
async def cron_1day_reminders():
    """
    Automated endpoint for 1-day reminders - called by cron job
    No authentication required as this is internal system call
    """
    try:
        logger.info("Automated 1-day reminders triggered by cron job")
        
        result = await NotificationService.send_1day_reminders()
        
        # Log results for monitoring
        if result.get("success"):
            logger.info(f"Cron 1-day reminders completed: {result.get('emails_sent')} sent, {result.get('failed_emails')} failed")
        else:
            logger.error(f"Cron 1-day reminders failed: {result.get('error')}")
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Unknown error"),
            "emails_sent": result.get("emails_sent", 0),
            "failed_emails": result.get("failed_emails", 0),
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord("", 0, "", 0, "", (), None))
        }
        
    except Exception as e:
        logger.error(f"Error in cron 1-day reminders: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "emails_sent": 0,
            "failed_emails": 0
        }

@router.post("/cron/15min-reminders")
async def cron_15min_reminders():
    """
    Automated endpoint for 15-minute reminders - called by cron job
    No authentication required as this is internal system call
    """
    try:
        logger.info("Automated 15-minute reminders triggered by cron job")
        
        result = await NotificationService.send_15min_reminders()
        
        # Log results for monitoring
        if result.get("success"):
            logger.info(f"Cron 15-min reminders completed: {result.get('emails_sent')} sent, {result.get('failed_emails')} failed")
        else:
            logger.error(f"Cron 15-min reminders failed: {result.get('error')}")
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", "Unknown error"),
            "emails_sent": result.get("emails_sent", 0),
            "failed_emails": result.get("failed_emails", 0),
            "timestamp": logger.handlers[0].formatter.formatTime(logger.makeRecord("", 0, "", 0, "", (), None))
        }
        
    except Exception as e:
        logger.error(f"Error in cron 15-min reminders: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "emails_sent": 0,
            "failed_emails": 0
        }
