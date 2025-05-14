# app/schemas/alert.py
from datetime import datetime
from pydantic import BaseModel

class AlertBase(BaseModel):
    camera_id: str
    score: float

class AlertCreate(AlertBase):
    pass

class AlertRead(AlertBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True
