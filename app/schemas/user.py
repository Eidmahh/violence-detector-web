# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from typing import Literal

# Base schema with fields common to reading and creating
class UserBase(BaseModel):
    email: EmailStr
    role: Literal['admin', 'user']

# Schema for user creation (input)
class UserCreate(UserBase):
    password: str

# Schema for user output/read
class UserOut(UserBase):
    id: int

    # Pydantic v2: allow reading from ORM objects
    model_config = {
        'from_attributes': True
    }

# Alias UserRead to UserOut for backward compatibility
UserRead = UserOut