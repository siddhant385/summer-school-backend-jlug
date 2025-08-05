# app/schemas/user_workshop.py

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.core.logger import setup_logger

log = setup_logger(__name__)


# 1. Register user to workshop
class RegisterUserToWorkshopSchema(BaseModel):
    user_id: UUID = Field(..., description="UUID of the user to register")
    workshop_id: UUID = Field(..., description="UUID of the workshop to register for")
    
    model_config = {"populate_by_name": True}


# 2. User-Workshop relationship response (matches DB schema exactly)
class UserWorkshopRelation(BaseModel):
    user_id: UUID = Field(..., description="User ID (primary key part 1)")
    workshop_id: UUID = Field(..., description="Workshop ID (primary key part 2)")
    created_at: datetime = Field(..., description="Registration timestamp")
    reminder_1day_sent: Optional[bool] = Field(None, description="Whether 1-day reminder was sent")
    reminder_15min_sent: Optional[bool] = Field(None, description="Whether 15-min reminder was sent")
    
    model_config = {"populate_by_name": True}


# 3. Workshop user details (for workshop participant list)
class WorkshopUser(BaseModel):
    user_id: UUID = Field(..., description="User UUID")
    name: Optional[str] = Field(None, description="User's name")
    email: str = Field(..., description="User's email address")
    profile_pic_url: Optional[str] = Field(None, description="User's profile picture URL")
    points: Optional[int] = Field(None, ge=0, description="User's points")
    role: Optional[str] = Field(None, description="User's role")
    reminder_1day_sent: Optional[bool] = Field(None, description="1-day reminder status")
    reminder_15min_sent: Optional[bool] = Field(None, description="15-min reminder status")
    created_at: datetime = Field(..., description="Registration date")
    
    model_config = {"populate_by_name": True}

class FetchWorkshopUsersResponse(BaseModel):
    workshop_id: UUID = Field(..., description="Workshop UUID")
    total_participants: int = Field(..., ge=0, description="Total number of participants")
    users: List[WorkshopUser] = Field(..., description="List of registered users")
    
    model_config = {"populate_by_name": True}


# 4. User's workshop details (for user's registered workshops)
class UserWorkshop(BaseModel):
    workshop_id: UUID = Field(..., description="Workshop UUID")
    title: Optional[str] = Field(None, description="Workshop title")
    description: Optional[str] = Field(None, description="Workshop description")
    technologies: Optional[List[str]] = Field(None, description="Workshop technologies array")
    conducted_by: Optional[str] = Field(None, description="Workshop conductor")
    scheduled_at: Optional[datetime] = Field(None, description="Workshop scheduled date and time")
    reminder_1day_sent: Optional[bool] = Field(None, description="1-day reminder status")
    reminder_15min_sent: Optional[bool] = Field(None, description="15-min reminder status")
    registration_date: datetime = Field(..., description="User registration date")
    
    model_config = {"populate_by_name": True}

class FetchUsersWorkshopsResponse(BaseModel):
    user_id: UUID = Field(..., description="User UUID")
    total_workshops: int = Field(..., ge=0, description="Total registered workshops count")
    workshops: List[UserWorkshop] = Field(..., description="List of user's workshops")
    
    model_config = {"populate_by_name": True}


# 5. Update reminder status
class UpdateReminderStatusSchema(BaseModel):
    user_id: UUID = Field(..., description="User UUID")
    workshop_id: UUID = Field(..., description="Workshop UUID")
    reminder_1day_sent: Optional[bool] = Field(None, description="1-day reminder sent status")
    reminder_15min_sent: Optional[bool] = Field(None, description="15-min reminder sent status")
    
    model_config = {"populate_by_name": True}


# 6. Registered User Registration Schema
class RegisteredUserRegistrationSchema(BaseModel):
    workshop_id: UUID = Field(..., description="Workshop ID to register for")
    
    model_config = {"populate_by_name": True}


# 7. Guest Registration Schema
class GuestRegistrationSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Guest's full name")
    email: str = Field(..., description="Guest's email address")
    workshop_id: UUID = Field(..., description="Workshop ID to register for")
    
    model_config = {"populate_by_name": True}


# 8. Registration Response Schema
class RegistrationResponseSchema(BaseModel):
    user_id: UUID = Field(..., description="Registered user ID")
    workshop_id: UUID = Field(..., description="Workshop ID")
    registration_date: datetime = Field(..., description="Registration timestamp")
    user_type: str = Field(..., description="Type of user: 'registered' or 'guest'")
    message: str = Field(..., description="Success message")
    
    model_config = {"populate_by_name": True}
