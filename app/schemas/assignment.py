from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Annotated, List
from datetime import datetime
from uuid import UUID
from enum import Enum

# Simple assignment status enum
class AssignmentStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    REVIEWED = "reviewed"
    REJECTED = "rejected"

# Base assignment model - simple and clean
class AssignmentBase(BaseModel):
    title: Optional[str] = None
    submit_link: Optional[str] = None
    user_id: UUID
    workshop_id: UUID
    status: AssignmentStatus = AssignmentStatus.PENDING
    feedback: Optional[str] = None
    marks: Optional[Annotated[int, Field(ge=0, le=100)]] = None

# For auto-creation when user enrolls in workshop
class AssignmentAutoCreate(BaseModel):
    """Schema for auto-creating assignment on workshop enrollment"""
    user_id: UUID
    workshop_id: UUID
    # Title and other fields will be set automatically

# For student submission
class AssignmentSubmit(BaseModel):
    """Schema for student submitting their assignment"""
    title: Annotated[str, Field(min_length=3, max_length=200, strip_whitespace=True)]
    submit_link: Annotated[str, Field(min_length=1, max_length=500, strip_whitespace=True)]
    
    @field_validator('submit_link')
    @classmethod
    def validate_submit_link(cls, v: str) -> str:
        """Validate submission link format"""
        v = v.strip()
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Submit link must be a valid URL starting with http:// or https://')
        return v

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is meaningful"""
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Title must be at least 3 characters long')
        return v

# For admin grading and feedback
class AssignmentGrade(BaseModel):
    """Schema for admin to grade and provide feedback"""
    status: AssignmentStatus
    feedback: Optional[Annotated[str, Field(max_length=1000, strip_whitespace=True)]] = None
    marks: Optional[Annotated[int, Field(ge=0, le=100)]] = None

    @field_validator('feedback')
    @classmethod
    def validate_feedback_for_reviewed(cls, v: Optional[str], info) -> Optional[str]:
        """Require feedback when marking as reviewed or rejected"""
        # Get status from the data being validated
        if hasattr(info, 'data') and info.data:
            status = info.data.get('status')
            if status in [AssignmentStatus.REVIEWED, AssignmentStatus.REJECTED]:
                if not v or len(v.strip()) < 5:
                    raise ValueError('Feedback is required when reviewing or rejecting assignments')
        return v.strip() if v else v

# Complete assignment model
class Assignment(AssignmentBase):
    """Complete assignment model with database fields"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# Enhanced response models with better structure
class AssignmentResponse(BaseModel):
    """Response for single assignment operations"""
    assignment: Assignment
    message: str
    success: bool = True

class AssignmentListResponse(BaseModel):
    """Response for assignment listing with pagination info"""
    assignments: List[Assignment]
    total_count: int
    workshop_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    page: int = 1
    per_page: int = 20
    has_next: bool = False

# Additional utility schema for assignment statistics
class AssignmentStats(BaseModel):
    """Statistics for workshop assignments"""
    total_assignments: int = 0
    submitted_count: int = 0
    under_review_count: int = 0
    reviewed_count: int = 0
    rejected_count: int = 0
    average_marks: Optional[float] = None
    workshop_id: UUID
