# app/api/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.security import get_current_active_user, is_admin, hash_password
from app.schemas.user import UserCreate, UserOut
from app.db.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    # 1. Only allow admins
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 2. Check for existing email
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 3. Create & save
    new_user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        role=user_in.role,        # e.g. "admin" or "user"
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user