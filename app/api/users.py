# app/api/users.py

from typing   import List

from fastapi  import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session    import get_db
from app.db.models     import User, UserRole
from app.schemas.user  import UserRead, UserCreate, UserUpdateRole
from app.services.security import hash_password
from app.api.auth     import get_current_active_admin

router = APIRouter()


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (Admin only)",
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_admin),    # only admins
):
    # Prevent duplicate emails
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    # Create user
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole(data.role),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "/",
    response_model=List[UserRead],
    summary="List all users (Admin only)",
)
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_admin),    # only admins
):
    return db.query(User).all()


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    summary="Update a user's role (Admin only)",
)
def update_user_role(
    user_id: int,
    data: UserUpdateRole,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_admin),    # only admins
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.role = UserRole(data.role)
    db.commit()
    db.refresh(user)
    return user
