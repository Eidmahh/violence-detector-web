# app/api/auth.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config     import settings
from app.db.session     import get_db
from app.db.models      import User, UserRole
from app.schemas.user   import UserCreate, UserRead
from app.schemas.auth   import ResetRequest, ResetPassword
from app.schemas.token  import Token, TokenPayload
from app.services.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    authenticate_user,
)

router = APIRouter(tags=["auth"])  # no prefix here

# use a relative tokenUrl that FastAPI will resolve to /auth/login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).count() > 0:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Initial signup only")
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token_data = {"sub": str(user.id), "role": user.role.value}
    access_token = create_access_token(token_data)
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        data = TokenPayload(**payload)
    except JWTError:
        raise credentials_exc

    user = db.get(User, int(data.sub))
    if not user:
        raise credentials_exc
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role is not UserRole.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin privileges required")
    return current_user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(data: ResetRequest, db: Session = Depends(get_db)):
    _ = db.query(User).filter_by(email=data.email).first()
    return {"msg": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(data.token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("sub")
    except JWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid reset token")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    user.password_hash = get_password_hash(data.new_password)
    db.commit()
    return {"msg": "Password reset successful"}
