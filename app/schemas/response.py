# In app/schemas/common.py
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, List

# Ye Pydantic ko batata hai ki 'T' kisi bhi type ka ho sakta hai
T = TypeVar('T')

class ResponseModel(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None