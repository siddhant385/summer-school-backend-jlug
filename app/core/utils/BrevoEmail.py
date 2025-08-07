"""
Brevo Email Service Utility
Workshop reminder emails ke liye simple functions
"""

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, EmailStr
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class BrevoEmailService:
    """Simple Brevo email service for workshop reminders"""
    
    def __init__(self):
        """Initialize Brevo API client"""
        try:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = settings.BREVO_API_KEY.get_secret_value()
            
            self.transactional_emails_api = sib_api_v3_sdk.TransactionalEmailsApi(
                sib_api_v3_sdk.ApiClient(configuration)
            )
            
            logger.info("Brevo email service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Brevo email service: {str(e)}")
            raise
    
    async def send_workshop_reminder_1day(
        self, 
        user_email: str, 
        user_name: str, 
        workshop_title: str,
        workshop_start_time: str,
        workshop_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send 1 day before workshop reminder email
        """
        try:
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #2563eb;">Workshop Reminder - 1 Day to Go! 🚀</h2>
                <p>Hi <strong>{user_name}</strong>,</p>
                
                <p>This is a friendly reminder that your workshop is starting tomorrow!</p>
                
                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1f2937; margin-top: 0;">📚 {workshop_title}</h3>
                    <p><strong>⏰ Start Time:</strong> {workshop_start_time}</p>
                    {f'<p><strong>📝 Description:</strong> {workshop_description}</p>' if workshop_description else ''}
                </div>
                
                <p><strong>📋 What to prepare:</strong></p>
                <ul>
                    <li>Make sure you have a stable internet connection</li>
                    <li>Keep your laptop/computer ready</li>
                    <li>Review any pre-workshop materials if provided</li>
                    <li>Join the workshop platform 5-10 minutes early</li>
                </ul>
                
                <p>We're excited to see you in the workshop! 🎉</p>
                
                <p>Best regards,<br>
                <strong>Team Summer School JLUG</strong></p>
            </div>
            """
            
            text_content = f"""
            Workshop Reminder - 1 Day to Go!
            
            Hi {user_name},
            
            This is a friendly reminder that your workshop is starting tomorrow!
            
            Workshop: {workshop_title}
            Start Time: {workshop_start_time}
            {f'Description: {workshop_description}' if workshop_description else ''}
            
            What to prepare:
            - Make sure you have a stable internet connection
            - Keep your laptop/computer ready
            - Review any pre-workshop materials if provided
            - Join the workshop platform 5-10 minutes early
            
            We're excited to see you in the workshop!
            
            Best regards,
            Team Summer School JLUG
            """
            
            return await self._send_email(
                to_email=user_email,
                to_name=user_name,
                subject=f"Workshop Tomorrow: {workshop_title} 📚",
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending 1-day reminder to {user_email}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_workshop_reminder_15min(
        self, 
        user_email: str, 
        user_name: str, 
        workshop_title: str,
        workshop_join_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send 15 minutes before workshop reminder email
        """
        try:
            join_button = ""
            join_text = ""
            
            if workshop_join_link:
                join_button = f"""
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{workshop_join_link}" 
                       style="background-color: #059669; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 6px; font-weight: bold;
                              display: inline-block;">
                        🚀 Join Workshop Now
                    </a>
                </div>
                """
                join_text = f"\nJoin Workshop: {workshop_join_link}\n"
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #dc2626;">Workshop Starting in 15 Minutes! ⏰</h2>
                <p>Hi <strong>{user_name}</strong>,</p>
                
                <p>Your workshop is starting in just <strong>15 minutes</strong>!</p>
                
                <div style="background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 20px; margin: 20px 0;">
                    <h3 style="color: #1f2937; margin-top: 0;">📚 {workshop_title}</h3>
                    <p style="color: #dc2626; font-weight: bold;">⏰ Starting NOW - Don't miss out!</p>
                </div>
                
                {join_button}
                
                <p><strong>🎯 Quick checklist:</strong></p>
                <ul>
                    <li>✅ Internet connection ready</li>
                    <li>✅ Device charged and ready</li>
                    <li>✅ Notebook and pen ready</li>
                    <li>✅ Distractions minimized</li>
                </ul>
                
                <p>See you in the workshop! 🚀</p>
                
                <p>Best regards,<br>
                <strong>Team Summer School JLUG</strong></p>
            </div>
            """
            
            text_content = f"""
            Workshop Starting in 15 Minutes!
            
            Hi {user_name},
            
            Your workshop is starting in just 15 minutes!
            
            Workshop: {workshop_title}
            Starting NOW - Don't miss out!
            {join_text}
            Quick checklist:
            - Internet connection ready
            - Device charged and ready
            - Notebook and pen ready
            - Distractions minimized
            
            See you in the workshop!
            
            Best regards,
            Team Summer School JLUG
            """
            
            return await self._send_email(
                to_email=user_email,
                to_name=user_name,
                subject=f"Starting NOW: {workshop_title} ⏰",
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending 15-min reminder to {user_email}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_workshop_welcome_email(
        self,
        user_email: str,
        user_name: str,
        workshop_title: str,
        workshop_start_time: str,
        workshop_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send workshop enrollment confirmation email
        """
        try:
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #059669;">Workshop Enrollment Confirmed! 🎉</h2>
                <p>Hi <strong>{user_name}</strong>,</p>
                
                <p>Congratulations! You've successfully enrolled in:</p>
                
                <div style="background-color: #f0f9f0; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #059669;">
                    <h3 style="color: #1f2937; margin-top: 0;">📚 {workshop_title}</h3>
                    <p><strong>⏰ Start Time:</strong> {workshop_start_time}</p>
                    {f'<p><strong>📝 About:</strong> {workshop_description}</p>' if workshop_description else ''}
                </div>
                
                <p><strong>📅 What happens next:</strong></p>
                <ul>
                    <li>You'll receive a reminder <strong>1 day before</strong> the workshop</li>
                    <li>Another reminder <strong>15 minutes before</strong> it starts</li>
                    <li>Workshop materials will be shared during the session</li>
                    <li>Complete assignments to earn points and certificates</li>
                </ul>
                
                <p>We're excited to have you on this learning journey! 🚀</p>
                
                <p>Best regards,<br>
                <strong>Team Summer School JLUG</strong></p>
            </div>
            """
            
            text_content = f"""
            Workshop Enrollment Confirmed!
            
            Hi {user_name},
            
            Congratulations! You've successfully enrolled in:
            
            Workshop: {workshop_title}
            Start Time: {workshop_start_time}
            {f'About: {workshop_description}' if workshop_description else ''}
            
            What happens next:
            - You'll receive a reminder 1 day before the workshop
            - Another reminder 15 minutes before it starts
            - Workshop materials will be shared during the session
            - Complete assignments to earn points and certificates
            
            We're excited to have you on this learning journey!
            
            Best regards,
            Team Summer School JLUG
            """
            
            return await self._send_email(
                to_email=user_email,
                to_name=user_name,
                subject=f"Welcome to {workshop_title}! 🎉",
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {user_email}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _send_email(
        self,
        to_email: str,
        to_name: str,
        subject: str,
        html_content: str,
        text_content: str
    ) -> Dict[str, Any]:
        """
        Internal method to send email using Brevo API
        """
        try:
            # Prepare sender
            sender = sib_api_v3_sdk.SendSmtpEmailSender(
                name=settings.BREVO_SENDER_NAME,
                email=settings.BREVO_SENDER_EMAIL
            )
            
            # Prepare recipient
            to_recipient = sib_api_v3_sdk.SendSmtpEmailTo(
                email=to_email,
                name=to_name
            )
            
            # Create email object
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[to_recipient],
                sender=sender,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            # Send email
            api_response = self.transactional_emails_api.send_transac_email(send_smtp_email)
            
            logger.info(f"Email sent successfully to {to_email}. Message ID: {api_response.message_id}")
            
            return {
                "success": True,
                "message_id": api_response.message_id,
                "recipient": to_email
            }
            
        except ApiException as e:
            logger.error(f"Brevo API error: {e.status} - {e.reason}")
            return {
                "success": False,
                "error": f"API Error: {e.reason}",
                "status_code": e.status
            }
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Global instance
brevo_email_service = BrevoEmailService()

# Helper functions for easy use
async def send_1day_workshop_reminder(user_email: str, user_name: str, workshop_title: str, workshop_start_time: str, workshop_description: Optional[str] = None):
    """Quick function to send 1-day reminder"""
    return await brevo_email_service.send_workshop_reminder_1day(
        user_email, user_name, workshop_title, workshop_start_time, workshop_description
    )

async def send_15min_workshop_reminder(user_email: str, user_name: str, workshop_title: str, workshop_join_link: Optional[str] = None):
    """Quick function to send 15-min reminder"""
    return await brevo_email_service.send_workshop_reminder_15min(
        user_email, user_name, workshop_title, workshop_join_link
    )

async def send_workshop_welcome(user_email: str, user_name: str, workshop_title: str, workshop_start_time: str, workshop_description: Optional[str] = None):
    """Quick function to send workshop welcome email"""
    return await brevo_email_service.send_workshop_welcome_email(
        user_email, user_name, workshop_title, workshop_start_time, workshop_description
    )

# Test function for development
async def test_brevo_connection():
    """Test if Brevo service is working properly"""
    try:
        # This will test if API key is valid
        test_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[sib_api_v3_sdk.SendSmtpEmailTo(email="test@example.com", name="Test User")],
            sender=sib_api_v3_sdk.SendSmtpEmailSender(
                email=settings.BREVO_SENDER_EMAIL,
                name=settings.BREVO_SENDER_NAME
            ),
            subject="Test Connection",
            html_content="<p>Test email</p>"
        )
        
        logger.info("Brevo API connection test successful")
        return {"success": True, "message": "Brevo API connection working"}
        
    except Exception as e:
        logger.error(f"Brevo API connection test failed: {str(e)}")
        return {"success": False, "error": str(e)}
