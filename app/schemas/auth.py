from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

class UserMetadata(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class TokenData(BaseModel):
    sub: UUID
    email: EmailStr
    user_metadata: UserMetadata = Field(..., alias="user_metadata")

    class Config:
        allow_population_by_field_name = True  # For using field name OR alias
