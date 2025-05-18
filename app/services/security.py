# app/services/security.py

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import User

# Use Argon2 (or bcrypt) — make sure you've installed passlib[argon2]
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hashes a plaintext password for storage.
    """
    return pwd_context.hash(password)
def get_password_hash(p: str) -> str:
    return hash_password(p)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against the stored hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> Optional[User]:
    """
    Fetches the user by email and verifies the password.
    Returns the User if successful, or None otherwise.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generates a JWT token with the given payload (e.g. {"sub": user.id, "role": user.role}).
    You can override the expiration via expires_delta.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
