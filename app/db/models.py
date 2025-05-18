import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean  # ← added Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"
    id             = Column(Integer, primary_key=True, index=True)
    email          = Column(String, unique=True, index=True, nullable=False)
    password_hash  = Column(String, nullable=False)
    role           = Column(Enum(UserRole), nullable=False, default=UserRole.viewer)
    is_active      = Column(Boolean, default=True)              # ← new column
    twofa_secret   = Column(String, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)
    alerts         = relationship("Alert", back_populates="user")

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.admin                      # ← new helper

class Alert(Base):
    __tablename__ = "alerts"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String, nullable=False)
    timestamp  = Column(DateTime, default=datetime.utcnow)
    user       = relationship("User", back_populates="alerts")
