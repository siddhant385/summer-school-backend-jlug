"""
Notification Service for Workshop Email Reminders
Simplified service for workshop email notifications with IST timezone support
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException, status
import logging

from app.core.db import get_db, get_db_admin
from app.core.utils.BrevoEmail import brevo_email_service

logger = logging.getLogger(__name__)

# IST timezone for proper time handling
IST = ZoneInfo("Asia/Kolkata")


class NotificationService:
    @staticmethod
    def send_1day_reminders() -> Dict[str, Any]:
        """
        Send 1-day reminder emails for workshops starting tomorrow
        """
        try:
            # Calculate time window for 1-day reminders (next 24 hours)
            now_ist = datetime.now(IST)
            next_24_hours = now_ist + timedelta(hours=24)
            
            logger.info(f"Checking for workshops starting within next 24 hours from {now_ist} to {next_24_hours} (IST)")
            
            db = get_db()
            
            # Get user enrollments that need 1-day reminders
            response = db.table("user_workshop").select("*").is_("reminder_1day_sent", False).execute()
            
            if not response.data:
                logger.info("No workshops found for 1-day reminders")
                return {"status": "success", "message": "No workshops found for 1-day reminders", "count": 0}
            
            # Get workshops data
            workshops_response = db.table("workshops").select("id, title, scheduled_at").execute()
            workshops_dict = {w["id"]: w for w in workshops_response.data} if workshops_response.data else {}
            
            # Get users data with correct schema - only 'name' column exists
            users_response = db.table("users").select("id, name, email").execute()
            users_dict = {u["id"]: u for u in users_response.data} if users_response.data else {}
            
            success_count = 0
            errors = []
            workshops_to_process = []
            
            # Filter workshops starting tomorrow
            for enrollment in response.data:
                workshop_id = enrollment.get("workshop_id")
                workshop = workshops_dict.get(workshop_id)
                
                if workshop and workshop.get("scheduled_at"):
                    # Parse workshop start time and convert to IST
                    start_time_str = workshop["scheduled_at"]
                    if start_time_str.endswith("Z"):
                        start_time_str = start_time_str.replace("Z", "+00:00")
                    
                    start_time = datetime.fromisoformat(start_time_str)
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=IST)
                    else:
                        start_time = start_time.astimezone(IST)
                    
                    # Check if workshop is starting within next 24 hours (flexible window)
                    # Send 1-day reminder only if workshop is within next 24 hours
                    time_until_workshop = start_time - now_ist
                    hours_until_workshop = time_until_workshop.total_seconds() / 3600
                    
                    # Send reminder only if workshop is within next 24 hours (1 day)
                    if 0 < hours_until_workshop <= 24:
                        workshops_to_process.append({
                            "enrollment": enrollment,
                            "workshop": workshop,
                            "start_time": start_time
                        })
            
            if not workshops_to_process:
                logger.info("No workshops starting within next 24 hours found for 1-day reminders")
                return {"status": "success", "message": "No workshops starting within next 24 hours found", "count": 0}
            
            # Send emails and update status
            for item in workshops_to_process:
                enrollment = item["enrollment"]
                workshop = item["workshop"]
                start_time = item["start_time"]
                
                try:
                    user_id = enrollment.get("user_id")
                    user = users_dict.get(user_id, {})
                    
                    # Fixed: Use 'name' column as per schema
                    name = user.get("name", "")
                    email = user.get("email", "")
                    title = workshop.get("title", "")
                    
                    if not email:
                        errors.append(f"No email found for user {user_id}")
                        continue
                    
                    # Send email with correct BrevoEmail method signature
                    email_sent = brevo_email_service.send_1day_workshop_reminder(
                        recipient_email=email,
                        recipient_name=name,
                        workshop_title=title,
                        workshop_date=start_time.strftime("%B %d, %Y"),  # "August 08, 2025"
                        workshop_time=start_time.strftime("%I:%M %p IST")  # "02:30 PM IST"
                    )
                    
                    if email_sent:
                        # Update reminder status using Supabase
                        db.table("user_workshop").update({
                            "reminder_1day_sent": True
                        }).eq("user_id", enrollment["user_id"]).eq("workshop_id", enrollment["workshop_id"]).execute()
                        
                        success_count += 1
                        logger.info(f"1-day reminder sent to {email} for workshop {title}")
                    else:
                        errors.append(f"Failed to send email to {email}")
                        
                except Exception as e:
                    error_msg = f"Error sending 1-day reminder: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue
            
            return {
                "status": "success", 
                "message": f"1-day reminders processed",
                "count": success_count,
                "total_found": len(workshops_to_process),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error in send_1day_reminders: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send 1-day reminders: {str(e)}"
            )
    
    @staticmethod
    def send_15min_reminders() -> Dict[str, Any]:
        """
        Send 15-minute reminder emails for workshops starting in 15 minutes
        """
        try:
            # Calculate time window for 15-minute reminders (next 15 minutes)
            now_ist = datetime.now(IST)
            next_15_minutes = now_ist + timedelta(minutes=15)
            
            logger.info(f"Checking for workshops starting within next 15 minutes from {now_ist} to {next_15_minutes} (IST)")
            
            db = get_db()
            
            # Get user enrollments that need 15-min reminders
            response = db.table("user_workshop").select("*").is_("reminder_15min_sent", False).execute()
            
            if not response.data:
                logger.info("No workshops found for 15-minute reminders")
                return {"status": "success", "message": "No workshops found for 15-minute reminders", "count": 0}
            
            # Get workshops data
            workshops_response = db.table("workshops").select("id, title, scheduled_at").execute()
            workshops_dict = {w["id"]: w for w in workshops_response.data} if workshops_response.data else {}
            
            # Get users data with correct schema - only 'name' column exists
            users_response = db.table("users").select("id, name, email").execute()
            users_dict = {u["id"]: u for u in users_response.data} if users_response.data else {}
            
            success_count = 0
            errors = []
            workshops_to_process = []
            
            # Filter workshops starting in 15 minutes
            for enrollment in response.data:
                workshop_id = enrollment.get("workshop_id")
                workshop = workshops_dict.get(workshop_id)
                
                if workshop and workshop.get("scheduled_at"):
                    # Parse workshop start time and convert to IST
                    start_time_str = workshop["scheduled_at"]
                    if start_time_str.endswith("Z"):
                        start_time_str = start_time_str.replace("Z", "+00:00")
                    
                    workshop_start = datetime.fromisoformat(start_time_str)
                    if workshop_start.tzinfo is None:
                        workshop_start = workshop_start.replace(tzinfo=IST)
                    else:
                        workshop_start = workshop_start.astimezone(IST)
                    
                    # Check if workshop is starting within next 15 minutes (flexible window)
                    # Send 15-min reminder only if workshop is within next 15 minutes
                    time_until_workshop = workshop_start - now_ist
                    minutes_until_workshop = time_until_workshop.total_seconds() / 60
                    
                    # Send reminder only if workshop is within next 15 minutes
                    if 0 < minutes_until_workshop <= 15:
                        workshops_to_process.append({
                            "enrollment": enrollment,
                            "workshop": workshop,
                            "start_time": workshop_start
                        })
            
            if not workshops_to_process:
                logger.info("No workshops starting within next 15 minutes found")
                return {"status": "success", "message": "No workshops starting within next 15 minutes", "count": 0}
            
            # Send emails and update status
            for item in workshops_to_process:
                enrollment = item["enrollment"]
                workshop = item["workshop"]
                start_time = item["start_time"]
                
                try:
                    user_id = enrollment.get("user_id")
                    user = users_dict.get(user_id, {})
                    
                    # Fixed: Use 'name' column as per schema
                    name = user.get("name", "")
                    email = user.get("email", "")
                    title = workshop.get("title", "")
                    
                    if not email:
                        errors.append(f"No email found for user {user_id}")
                        continue
                    
                    # Send email with correct BrevoEmail method signature
                    email_sent = brevo_email_service.send_15min_workshop_reminder(
                        recipient_email=email,
                        recipient_name=name,
                        workshop_title=title
                    )
                    
                    if email_sent:
                        # Update reminder status using Supabase
                        db.table("user_workshop").update({
                            "reminder_15min_sent": True
                        }).eq("user_id", enrollment["user_id"]).eq("workshop_id", enrollment["workshop_id"]).execute()
                        
                        success_count += 1
                        logger.info(f"15-min reminder sent to {email} for workshop {title}")
                    else:
                        errors.append(f"Failed to send email to {email}")
                        
                except Exception as e:
                    error_msg = f"Error sending 15-min reminder: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue
            
            return {
                "status": "success", 
                "message": f"15-minute reminders processed",
                "count": success_count,
                "total_found": len(workshops_to_process),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error in send_15min_reminders: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send 15-minute reminders: {str(e)}"
            )
    
    @staticmethod
    def update_reminder_status(
        user_id: UUID,
        workshop_id: UUID,
        reminder_1day_sent: Optional[bool] = None,
        reminder_15min_sent: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update reminder status in database using Supabase client
        """
        try:
            db = get_db()
            
            # Prepare update data
            update_data = {}
            if reminder_1day_sent is not None:
                update_data["reminder_1day_sent"] = reminder_1day_sent
            if reminder_15min_sent is not None:
                update_data["reminder_15min_sent"] = reminder_15min_sent
            
            if not update_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No reminder status to update"
                )
            
            # Update database using Supabase
            response = db.table("user_workshop").update(update_data).eq(
                "user_id", str(user_id)
            ).eq("workshop_id", str(workshop_id)).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User-workshop registration not found"
                )
            
            logger.info(f"Reminder status updated for user {user_id}, workshop {workshop_id}: {update_data}")
            
            return {
                "success": True,
                "message": "Reminder status updated successfully",
                "updated_fields": update_data
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating reminder status: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating reminder status: {str(e)}"
            )
    
    @staticmethod
    def get_notification_stats() -> Dict[str, Any]:
        """
        Get statistics about notifications using simple approach
        """
        try:
            now_ist = datetime.now(IST)
            db = get_db()
            
            # First get all user_workshop records
            response = db.table("user_workshop").select("*").execute()
            
            if not response.data:
                logger.warning("No enrollment data found")
                return {
                    "status": "success",
                    "timestamp_ist": now_ist.strftime("%Y-%m-%d %I:%M %p IST"),
                    "stats": {
                        "total_active_enrollments": 0,
                        "reminders_sent": {"1_day": 0, "15_minute": 0},
                        "reminders_pending": {"1_day": 0, "15_minute": 0}
                    }
                }
            
            # Get all workshops to check dates
            workshops_response = db.table("workshops").select("id, scheduled_at").execute()
            workshops_dict = {w["id"]: w for w in workshops_response.data} if workshops_response.data else {}
            
            # Calculate stats
            sent_1day = 0
            sent_15min = 0
            pending_1day = 0
            pending_15min = 0
            total_active = 0
            
            for enrollment in response.data:
                workshop_id = enrollment.get("workshop_id")
                workshop = workshops_dict.get(workshop_id)
                
                if workshop and workshop.get("scheduled_at"):
                    # Parse workshop start time
                    start_time_str = workshop["scheduled_at"]
                    if start_time_str.endswith("Z"):
                        start_time_str = start_time_str.replace("Z", "+00:00")
                    
                    workshop_start = datetime.fromisoformat(start_time_str)
                    
                    # Convert to naive datetime for comparison with IST now
                    if workshop_start.tzinfo:
                        workshop_start_naive = workshop_start.astimezone(IST).replace(tzinfo=None)
                    else:
                        workshop_start_naive = workshop_start
                    
                    now_ist_naive = now_ist.replace(tzinfo=None)
                    
                    # Only count future workshops
                    if workshop_start_naive > now_ist_naive:
                        total_active += 1
                        
                        # Count 1-day reminders
                        if enrollment.get("reminder_1day_sent"):
                            sent_1day += 1
                        else:
                            pending_1day += 1
                        
                        # Count 15-min reminders  
                        if enrollment.get("reminder_15min_sent"):
                            sent_15min += 1
                        else:
                            pending_15min += 1
            
            return {
                "status": "success",
                "timestamp_ist": now_ist.strftime("%Y-%m-%d %I:%M %p IST"),
                "stats": {
                    "total_active_enrollments": total_active,
                    "reminders_sent": {
                        "1_day": sent_1day,
                        "15_minute": sent_15min
                    },
                    "reminders_pending": {
                        "1_day": pending_1day,
                        "15_minute": pending_15min
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get notification stats: {str(e)}"
            )
