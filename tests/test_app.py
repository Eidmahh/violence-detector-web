# tests/test_app.py

import pytest
from fastapi.testclient import TestClient

# 0) Stub out the detector so background tasks don't load a real model
from app.services.detector import ViolenceDetector
ViolenceDetector.run = lambda self, *args, **kwargs: None

from app.main import app
from app.api.auth import get_current_active_user, get_current_active_admin

# 1) Override auth dependencies so we don’t need real JWTs or a DB user
def fake_user():
    class User:
        email = "test@example.com"
        role = type("R", (), {"name": "admin"})
    return User()

app.dependency_overrides[get_current_active_user] = fake_user
app.dependency_overrides[get_current_active_admin] = fake_user

client = TestClient(app)

def test_root_page():
    """GET / should return the dashboard HTML."""
    res = client.get("/")
    assert res.status_code == 200
    assert "Welcome to the Violence Detector" in res.text

def test_healthz():
    """GET /healthz should return status ok."""
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_start_detection():
    """POST /start-detection should launch the detector."""
    res = client.post("/start-detection")
    assert res.status_code == 200
    assert res.json()["message"] == "Detection started"
