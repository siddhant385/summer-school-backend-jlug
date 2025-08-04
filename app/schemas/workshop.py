# app/schemas/workshop.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from zoneinfo import ZoneInfo

# 🇮🇳 Indian timezone setup
IST = ZoneInfo("Asia/Kolkata")

def get_current_ist() -> datetime:
    """Get current time in Indian Standard Time"""
    return datetime.now(IST)

# 🔹 1. Enhanced Base schema - matching your database
class WorkshopBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=200, description="Workshop title")
    description: Optional[str] = Field(None, max_length=2000, description="Workshop description")
    technologies: Optional[List[str]] = Field(default_factory=list, description="Technologies covered")
    conducted_by: str = Field(..., min_length=2, max_length=100, description="Instructor name")
    scheduled_at: datetime = Field(..., description="Workshop schedule (IST)")

    @field_validator('scheduled_at')
    @classmethod
    def validate_future_schedule(cls, v: datetime) -> datetime:
        """Validate workshop is scheduled for future in IST"""
        current_ist = get_current_ist()
        
        # Convert to IST if timezone-naive
        if v.tzinfo is None:
            v = v.replace(tzinfo=IST)
        
        # Convert to IST for comparison
        v_ist = v.astimezone(IST)
        
        if v_ist <= current_ist:
            raise ValueError('Workshop must be scheduled for the future (IST)')
        
        return v_ist

# 🔹 2. Create schema - for POST /workshops
class WorkshopCreate(WorkshopBase):
    pass

# 🔹 3. Update schema - for PATCH /workshops/{id}
class WorkshopUpdate(BaseModel):
    """
    Workshop update schema - only real fields that can be modified.
    Computed fields (is_upcoming, time_until_workshop, scheduled_at_ist) 
    are automatically calculated and should NOT be included in updates.
    """
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    technologies: Optional[List[str]] = None
    conducted_by: Optional[str] = Field(None, min_length=2, max_length=100)
    scheduled_at: Optional[datetime] = None
    
    @field_validator('scheduled_at')
    @classmethod
    def validate_future_schedule(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate workshop is scheduled for future in IST"""
        if v is None:
            return v
            
        current_ist = get_current_ist()
        
        # Convert to IST if timezone-naive
        if v.tzinfo is None:
            v = v.replace(tzinfo=IST)
        
        # Convert to IST for comparison
        v_ist = v.astimezone(IST)
        
        if v_ist <= current_ist:
            raise ValueError('Workshop must be scheduled for the future (IST)')
        
        return v_ist

# 🔹 4. Full output schema - for GET responses
class WorkshopOut(WorkshopBase):
    """
    Workshop output schema with computed fields.
    
    Computed fields are automatically calculated:
    - is_upcoming: Whether workshop is in future (auto-calculated)
    - time_until_workshop: Human-readable time remaining (auto-calculated)
    - scheduled_at_ist: IST formatted date string (auto-calculated)
    
    These should never be manually set - they're computed from scheduled_at.
    """
    id: UUID
    created_at: datetime
    
    # 🔄 Computed fields (automatically calculated)
    is_upcoming: bool = True
    time_until_workshop: Optional[str] = None  # "2 days, 3 hours"
    scheduled_at_ist: Optional[str] = None  # Human readable IST time
    
    @field_validator('created_at', mode='before')
    @classmethod
    def convert_created_at_to_ist(cls, v):
        """Convert created_at to IST"""
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace('Z', '+00:00'))
        if v.tzinfo is None:
            v = v.replace(tzinfo=ZoneInfo("UTC"))
        return v.astimezone(IST)
    
    @field_validator('scheduled_at', mode='before')
    @classmethod
    def convert_scheduled_at_to_ist(cls, v):
        """Convert scheduled_at to IST"""
        if isinstance(v, str):
            v = datetime.fromisoformat(v.replace('Z', '+00:00'))
        if v.tzinfo is None:
            v = v.replace(tzinfo=IST)
        return v.astimezone(IST)
    
    def model_post_init(self, __context) -> None:
        """Calculate computed fields after model initialization"""
        current_ist = get_current_ist()
        
        # Check if upcoming
        self.is_upcoming = self.scheduled_at > current_ist
        
        # Calculate time until workshop
        if self.is_upcoming:
            time_diff = self.scheduled_at - current_ist
            days = time_diff.days
            hours = time_diff.seconds // 3600
            minutes = (time_diff.seconds % 3600) // 60
            
            if days > 0:
                self.time_until_workshop = f"{days} days, {hours} hours"
            elif hours > 0:
                self.time_until_workshop = f"{hours} hours, {minutes} minutes"
            else:
                self.time_until_workshop = f"{minutes} minutes"
        else:
            self.time_until_workshop = "Past"
        
        # Human readable IST time
        self.scheduled_at_ist = self.scheduled_at.strftime("%d %B %Y, %I:%M %p IST")
    
    class Config:
        from_attributes = True

# 🔹 5. Workshop list schema - for paginated results
class WorkshopList(BaseModel):
    workshops: List[WorkshopOut]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

# 🔹 6. Workshop search/filter schema
class WorkshopFilters(BaseModel):
    search: Optional[str] = Field(None, description="Search in title and description")
    technology: Optional[str] = Field(None, description="Filter by specific technology")
    instructor: Optional[str] = Field(None, description="Filter by instructor name")
    from_date: Optional[datetime] = Field(None, description="Filter workshops from this date (IST)")
    to_date: Optional[datetime] = Field(None, description="Filter workshops until this date (IST)")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @field_validator('from_date', 'to_date')
    @classmethod
    def convert_to_ist(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Convert filter dates to IST"""
        if v is None:
            return v
        if v.tzinfo is None:
            v = v.replace(tzinfo=IST)
        return v.astimezone(IST)

# 🔹 7. Workshop statistics schema
class WorkshopStats(BaseModel):
    total_workshops: int
    upcoming_workshops: int
    past_workshops: int
    popular_technologies: List[dict]  # [{"tech": "Python", "count": 5}]
    active_instructors: int
    next_workshop: Optional[WorkshopOut] = None
    current_time_ist: str  # Current IST time for reference

# 🔹 8. Workshop timezone helper schema
class WorkshopTimezone(BaseModel):
    """Helper schema for timezone conversions"""
    utc_time: datetime
    ist_time: datetime
    formatted_ist: str
    
    @classmethod
    def from_utc(cls, utc_time: datetime) -> "WorkshopTimezone":
        """Create from UTC time"""
        if utc_time.tzinfo is None:
            utc_time = utc_time.replace(tzinfo=ZoneInfo("UTC"))
        
        ist_time = utc_time.astimezone(IST)
        formatted_ist = ist_time.strftime("%d %B %Y, %I:%M %p IST")
        
        return cls(
            utc_time=utc_time,
            ist_time=ist_time,
            formatted_ist=formatted_ist
        )