# app/api/alerts.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import Alert, User           # ← add User here
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
    current_user: User = Depends(get_current_active_user),
):
    alert = Alert(
        **data.dict(),
        user_id=current_user.id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

