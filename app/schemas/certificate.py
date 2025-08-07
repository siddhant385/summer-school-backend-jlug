from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# Main certificate model for display
class Certificate(BaseModel):
    """Certificate model for user display only"""
    id: int
    created_at: datetime
    user_id: UUID
    workshop_id: UUID
    certificate_url: Optional[str] = None
    
    # Optional: Workshop info can be included for better UX
    workshop_title: Optional[str] = None
    workshop_conducted_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# Response models for API
class CertificateResponse(BaseModel):
    """Response for single certificate"""
    certificate: Certificate
    message: str = "Certificate retrieved successfully"

class CertificateListResponse(BaseModel):
    """Response for user's certificates list"""
    certificates: List[Certificate]
    total_count: int
    user_id: UUID
    message: str = "User certificates retrieved successfully"
