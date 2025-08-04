from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from app.core.logger import setup_logger

log = setup_logger(__name__)

class UserMetadata(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class TokenData(BaseModel):
    sub: UUID
    email: EmailStr
    user_metadata: UserMetadata = Field(..., alias="user_metadata")

    class Config:
        populate_by_name = True  # For using field name OR alias (Pydantic v2)
