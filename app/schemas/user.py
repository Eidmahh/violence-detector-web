# app/schemas/user.py
from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str
    role: str  # "admin" or "viewer"

class UserRead(BaseModel):
    id: int
    email: str
    role: str

    class Config:
        from_attributes = True

class UserUpdateRole(BaseModel):
    role: str
