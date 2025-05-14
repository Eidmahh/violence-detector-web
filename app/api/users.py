# app/api/users.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, UserRole
from app.schemas.user import UserRead, UserUpdateRole
from app.api.auth import get_current_active_admin

router = APIRouter()

@router.get("/", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@router.patch("/{user_id}/role", response_model=UserRead)
def update_user_role(
    user_id: int,
    data: UserUpdateRole,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.role = UserRole(data.role)
    db.commit()
    db.refresh(user)
    return user
