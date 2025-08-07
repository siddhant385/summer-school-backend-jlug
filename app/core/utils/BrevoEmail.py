"""
Brevo Email Service Utility
Workshop reminder emails ke liye simple functions - Only 1day and 15min reminders
"""

# Main imports jo hamesha chahiye
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from typing import Dict, Optional, Any
import logging

# Global logger
logger = logging.getLogger(__name__)

# Settings - will be imported conditionally
settings = None

# Import settings only when used as module
if __name__ != "__main__":
    from app.core.config import settings


class BrevoEmailService:
    def __init__(self, api_key=None, sender_email=None):
        # Use provided settings or fall back to global settings
        if api_key and sender_email:
            self.api_key = api_key
            self.sender_email = sender_email
        else:
            if settings is None:
                raise ValueError("Settings not available. Provide api_key and sender_email manually.")
            self.api_key = settings.BREVO_API_KEY.get_secret_value()
            self.sender_email = settings.BREVO_SENDER_EMAIL
            
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = self.api_key
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    def _send_email(self, 
                   recipient_email: str, 
                   recipient_name: str,
                   subject: str, 
                   html_content: str, 
                   sender_name: str = "Workshop Team") -> bool:
        """
        Core email sending function
        """
        try:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": recipient_email, "name": recipient_name}],
                subject=subject,
                html_content=html_content,
                sender={"name": sender_name, "email": self.sender_email}
            )
            
            response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except ApiException as e:
            logger.error(f"Email sending failed: {e}")
            return False

    def send_1day_workshop_reminder(self, 
                                  recipient_email: str,
                                  recipient_name: str,
                                  workshop_title: str,
                                  workshop_date: str,
                                  workshop_time: str) -> bool:
        """
        1 day pehle workshop reminder
        """
        subject = f"Tomorrow: {workshop_title} starts!"
        
        html_content = f"""
        <html>
        <body>
            <h2>Workshop Reminder - Starting Tomorrow!</h2>
            <p>Hi {recipient_name},</p>
            
            <p>This is a friendly reminder that your workshop starts <strong>tomorrow</strong>!</p>
            
            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>{workshop_title}</h3>
                <p><strong>Date:</strong> {workshop_date}</p>
                <p><strong>Time:</strong> {workshop_time}</p>
            </div>
            
            <p>Please make sure you're ready to join on time. We're excited to see you!</p>
            
            <p>Best regards,<br>
            Workshop Team</p>
        </body>
        </html>
        """
        
        return self._send_email(recipient_email, recipient_name, subject, html_content)

    def send_15min_workshop_reminder(self, 
                                   recipient_email: str,
                                   recipient_name: str,
                                   workshop_title: str) -> bool:
        """
        15 minute pehle workshop reminder
        """
        subject = f"Starting Soon: {workshop_title}"
        
        html_content = f"""
        <html>
        <body>
            <h2>Workshop Starting in 15 Minutes!</h2>
            <p>Hi {recipient_name},</p>
            
            <p>Your workshop <strong>"{workshop_title}"</strong> is starting in just <strong>15 minutes</strong>!</p>
            
            <p>Please join the session now to ensure you don't miss anything important.</p>
            
            <p>See you soon!<br>
            Workshop Team</p>
        </body>
        </html>
        """
        
        return self._send_email(recipient_email, recipient_name, subject, html_content)


# Global instance - will be created when settings are available
brevo_email_service = None
if settings is not None:
    brevo_email_service = BrevoEmailService()
