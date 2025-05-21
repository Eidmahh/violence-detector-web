# app/schemas/alert.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class AlertBase(BaseModel):
    image_path: str

class AlertCreate(AlertBase):
    """Only need the path; camera_id & score are determined server-side."""
    pass

class AlertRead(AlertBase):
    id: int
    timestamp: datetime
    user_id: Optional[int]

    class Config:
        from_attributes = True