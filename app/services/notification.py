"""
Notification Service for Workshop Email Reminders
Handles email notifications for workshop reminders and updates database status
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import HTTPException, status
import logging

from app.core.db import get_db, get_db_admin
from app.core.utils.BrevoEmail import (
    send_1day_workshop_reminder,
    send_15min_workshop_reminder, 
    send_workshop_welcome
)
from app.services.user_workshop import UserWorkshopService
from app.schemas.user_workshop import UpdateReminderStatusSchema

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling workshop email notifications"""
    
    @staticmethod
    async def get_workshops_for_1day_reminder() -> List[Dict[str, Any]]:
        """
        Get workshops that need 1-day reminder emails
        Returns workshops starting in 24 hours with users who haven't received 1-day reminder
        """
        try:
            # Calculate time range for workshops starting in ~24 hours
            tomorrow = datetime.now() + timedelta(days=1)
            start_time = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = tomorrow.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            db = get_db()
            
            # Get workshops starting tomorrow with enrolled users who haven't received 1-day reminder
            response = db.table("user_workshop").select("""
                user_id,
                workshop_id,
                reminder_1day_sent,
                user:users(id, name, email),
                workshop:workshops(id, title, description, start_time, end_time)
            """).eq("reminder_1day_sent", False).execute()
            
            if not response.data:
                logger.info("No users found requiring 1-day reminders")
                return []
            
            # Filter for workshops starting tomorrow
            filtered_data = []
            for item in response.data:
                workshop = item.get("workshop")
                if workshop and workshop.get("start_time"):
                    workshop_start = datetime.fromisoformat(workshop["start_time"].replace("Z", "+00:00"))
                    if start_time <= workshop_start <= end_time:
                        filtered_data.append(item)
            
            logger.info(f"Found {len(filtered_data)} users requiring 1-day reminders")
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error fetching workshops for 1-day reminder: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching workshops for reminder: {str(e)}"
            )
    
    @staticmethod
    async def get_workshops_for_15min_reminder() -> List[Dict[str, Any]]:
        """
        Get workshops that need 15-minute reminder emails
        Returns workshops starting in 15 minutes with users who haven't received 15-min reminder
        """
        try:
            # Calculate time range for workshops starting in ~15 minutes
            now = datetime.now()
            start_time = now + timedelta(minutes=10)  # 10-20 minute window
            end_time = now + timedelta(minutes=20)
            
            db = get_db()
            
            # Get workshops starting soon with enrolled users who haven't received 15-min reminder
            response = db.table("user_workshop").select("""
                user_id,
                workshop_id, 
                reminder_15min_sent,
                user:users(id, name, email),
                workshop:workshops(id, title, description, start_time, end_time, meeting_link)
            """).eq("reminder_15min_sent", False).execute()
            
            if not response.data:
                logger.info("No users found requiring 15-minute reminders")
                return []
            
            # Filter for workshops starting in ~15 minutes
            filtered_data = []
            for item in response.data:
                workshop = item.get("workshop")
                if workshop and workshop.get("start_time"):
                    workshop_start = datetime.fromisoformat(workshop["start_time"].replace("Z", "+00:00"))
                    if start_time <= workshop_start <= end_time:
                        filtered_data.append(item)
            
            logger.info(f"Found {len(filtered_data)} users requiring 15-minute reminders")
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error fetching workshops for 15-min reminder: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error fetching workshops for reminder: {str(e)}"
            )
    
    @staticmethod
    async def send_1day_reminders() -> Dict[str, Any]:
        """
        Send 1-day reminder emails to all eligible users and update database
        """
        try:
            workshops_data = await NotificationService.get_workshops_for_1day_reminder()
            
            if not workshops_data:
                return {
                    "success": True,
                    "message": "No 1-day reminders to send",
                    "emails_sent": 0,
                    "failed_emails": 0
                }
            
            emails_sent = 0
            failed_emails = 0
            results = []
            
            for item in workshops_data:
                try:
                    user = item.get("user")
                    workshop = item.get("workshop")
                    
                    if not user or not workshop:
                        logger.warning(f"Invalid user or workshop data: {item}")
                        failed_emails += 1
                        continue
                    
                    # Send email
                    email_result = await send_1day_workshop_reminder(
                        user_email=user["email"],
                        user_name=user["name"],
                        workshop_title=workshop["title"],
                        workshop_start_time=workshop["start_time"],
                        workshop_description=workshop.get("description")
                    )
                    
                    if email_result.get("success"):
                        # Update database to mark reminder as sent
                        await NotificationService.update_reminder_status(
                            user_id=UUID(item["user_id"]),
                            workshop_id=UUID(item["workshop_id"]),
                            reminder_1day_sent=True
                        )
                        emails_sent += 1
                        results.append({
                            "user_email": user["email"],
                            "workshop_title": workshop["title"],
                            "status": "sent",
                            "message_id": email_result.get("message_id")
                        })
                        logger.info(f"1-day reminder sent to {user['email']} for workshop {workshop['title']}")
                    else:
                        failed_emails += 1
                        results.append({
                            "user_email": user["email"],
                            "workshop_title": workshop["title"],
                            "status": "failed",
                            "error": email_result.get("error")
                        })
                        logger.error(f"Failed to send 1-day reminder to {user['email']}: {email_result.get('error')}")
                    
                except Exception as e:
                    failed_emails += 1
                    logger.error(f"Error processing 1-day reminder for user {item.get('user_id')}: {str(e)}")
            
            return {
                "success": True,
                "message": f"1-day reminders processed: {emails_sent} sent, {failed_emails} failed",
                "emails_sent": emails_sent,
                "failed_emails": failed_emails,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error sending 1-day reminders: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "emails_sent": 0,
                "failed_emails": 0
            }
    
    @staticmethod
    async def send_15min_reminders() -> Dict[str, Any]:
        """
        Send 15-minute reminder emails to all eligible users and update database
        """
        try:
            workshops_data = await NotificationService.get_workshops_for_15min_reminder()
            
            if not workshops_data:
                return {
                    "success": True,
                    "message": "No 15-minute reminders to send",
                    "emails_sent": 0,
                    "failed_emails": 0
                }
            
            emails_sent = 0
            failed_emails = 0
            results = []
            
            for item in workshops_data:
                try:
                    user = item.get("user")
                    workshop = item.get("workshop")
                    
                    if not user or not workshop:
                        logger.warning(f"Invalid user or workshop data: {item}")
                        failed_emails += 1
                        continue
                    
                    # Send email
                    email_result = await send_15min_workshop_reminder(
                        user_email=user["email"],
                        user_name=user["name"],
                        workshop_title=workshop["title"],
                        workshop_join_link=workshop.get("meeting_link")
                    )
                    
                    if email_result.get("success"):
                        # Update database to mark reminder as sent
                        await NotificationService.update_reminder_status(
                            user_id=UUID(item["user_id"]),
                            workshop_id=UUID(item["workshop_id"]),
                            reminder_15min_sent=True
                        )
                        emails_sent += 1
                        results.append({
                            "user_email": user["email"],
                            "workshop_title": workshop["title"],
                            "status": "sent",
                            "message_id": email_result.get("message_id")
                        })
                        logger.info(f"15-min reminder sent to {user['email']} for workshop {workshop['title']}")
                    else:
                        failed_emails += 1
                        results.append({
                            "user_email": user["email"],
                            "workshop_title": workshop["title"],
                            "status": "failed",
                            "error": email_result.get("error")
                        })
                        logger.error(f"Failed to send 15-min reminder to {user['email']}: {email_result.get('error')}")
                    
                except Exception as e:
                    failed_emails += 1
                    logger.error(f"Error processing 15-min reminder for user {item.get('user_id')}: {str(e)}")
            
            return {
                "success": True,
                "message": f"15-minute reminders processed: {emails_sent} sent, {failed_emails} failed",
                "emails_sent": emails_sent,
                "failed_emails": failed_emails,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error sending 15-minute reminders: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "emails_sent": 0,
                "failed_emails": 0
            }
    
    @staticmethod
    async def send_welcome_email(
        user_id: UUID,
        workshop_id: UUID
    ) -> Dict[str, Any]:
        """
        Send workshop welcome email to a specific user
        Used when user enrolls in a workshop
        """
        try:
            db = get_db()
            
            # Get user and workshop details
            response = db.table("user_workshop").select("""
                user:users(id, name, email),
                workshop:workshops(id, title, description, start_time, end_time)
            """).eq("user_id", str(user_id)).eq("workshop_id", str(workshop_id)).execute()
            
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User-workshop registration not found"
                )
            
            item = response.data[0]
            user = item.get("user")
            workshop = item.get("workshop")
            
            if not user or not workshop:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User or workshop details not found"
                )
            
            # Send welcome email
            email_result = await send_workshop_welcome(
                user_email=user["email"],
                user_name=user["name"],
                workshop_title=workshop["title"],
                workshop_start_time=workshop["start_time"],
                workshop_description=workshop.get("description")
            )
            
            if email_result.get("success"):
                logger.info(f"Welcome email sent to {user['email']} for workshop {workshop['title']}")
                return {
                    "success": True,
                    "message": "Welcome email sent successfully",
                    "user_email": user["email"],
                    "workshop_title": workshop["title"],
                    "message_id": email_result.get("message_id")
                }
            else:
                logger.error(f"Failed to send welcome email to {user['email']}: {email_result.get('error')}")
                return {
                    "success": False,
                    "error": email_result.get("error"),
                    "user_email": user["email"],
                    "workshop_title": workshop["title"]
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error sending welcome email for user {user_id}, workshop {workshop_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error sending welcome email: {str(e)}"
            )
    
    @staticmethod
    async def update_reminder_status(
        user_id: UUID,
        workshop_id: UUID,
        reminder_1day_sent: Optional[bool] = None,
        reminder_15min_sent: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Update reminder status in database after sending emails
        """
        try:
            db = get_db_admin()
            
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
            
            # Update database
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
    async def get_notification_stats() -> Dict[str, Any]:
        """
        Get statistics about notification status for monitoring
        """
        try:
            db = get_db()
            
            # Get total enrollments
            total_response = db.table("user_workshop").select("*", count="exact").execute()
            total_enrollments = total_response.count
            
            # Get 1-day reminders sent
            reminder_1day_response = db.table("user_workshop").select("*", count="exact").eq("reminder_1day_sent", True).execute()
            reminders_1day_sent = reminder_1day_response.count
            
            # Get 15-min reminders sent
            reminder_15min_response = db.table("user_workshop").select("*", count="exact").eq("reminder_15min_sent", True).execute()
            reminders_15min_sent = reminder_15min_response.count
            
            # Get pending reminders for tomorrow
            tomorrow_data = await NotificationService.get_workshops_for_1day_reminder()
            pending_1day = len(tomorrow_data)
            
            # Get pending reminders for next 15 minutes
            soon_data = await NotificationService.get_workshops_for_15min_reminder()
            pending_15min = len(soon_data)
            
            return {
                "success": True,
                "stats": {
                    "total_enrollments": total_enrollments,
                    "reminders_1day_sent": reminders_1day_sent,
                    "reminders_15min_sent": reminders_15min_sent,
                    "pending_1day_reminders": pending_1day,
                    "pending_15min_reminders": pending_15min,
                    "completion_rates": {
                        "1day_reminder_rate": (reminders_1day_sent / total_enrollments * 100) if total_enrollments > 0 else 0,
                        "15min_reminder_rate": (reminders_15min_sent / total_enrollments * 100) if total_enrollments > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting notification stats: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
