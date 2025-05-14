# app/schemas/user.py

from pydantic import BaseModel, EmailStr, constr
from typing import Literal
from app.db.models import UserRole

# used by signup
class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8)

# used for listing / reading back
class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: UserRole

    class Config:
        orm_mode = True

# used by admin to update someone's role
class UserUpdateRole(BaseModel):
    role: Literal["admin", "viewer"]
