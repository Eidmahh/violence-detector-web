# app/api/auth.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.db.session import SessionLocal
from app.db.models import User, UserRole
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import LoginRequest, ResetRequest, ResetPassword
from app.schemas.token import Token, TokenPayload
from app.services.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter( tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate, db: Session = Depends(get_db)):
    # Only allow the very first user to self-register as admin
    if db.query(User).count() > 0:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Initial signup only")
    if db.query(User).filter_by(email=data.email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole.admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    # authenticate just like before, but using credentials.username & credentials.password
    user = authenticate_user(db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect credentials")
    access_token = create_access_token({"sub": user.email, "role": user.role})
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

    user = db.query(User).get(int(data.sub))
    if not user:
        raise credentials_exc
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    # e.g. if current_user.is_blocked: raise HTTPException(...)
    return current_user


def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role is not UserRole.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Admin privileges required",
        )
    return current_user


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(data: ResetRequest, db: Session = Depends(get_db)):
    # TODO: generate a reset token, email it to the user
    user = db.query(User).filter_by(email=data.email).first()
    if not user:
        # don't reveal that the email is unknown
        return {"msg": "If that email is registered, a reset link has been sent."}
    # generate and send reset token…
    return {"msg": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(data: ResetPassword, db: Session = Depends(get_db)):
    # TODO: verify the token, update the user's password
    # Example placeholder logic:
    try:
        payload = jwt.decode(data.token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("sub")
    except JWTError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid reset token")
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"msg": "Password reset successful"}
