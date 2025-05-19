# app/api/alerts.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
# If you meant your SQLAlchemy User model:
from app.db.models import User

from app.db.session import get_db
from app.db.models import Alert
from app.schemas.alert import AlertRead, AlertCreate
from app.api.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=List[AlertRead])
def list_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).all()

@router.post("/", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
def create_alert(
    data: AlertCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
):
    alert = Alert(**data.dict())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert
