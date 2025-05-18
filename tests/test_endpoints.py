import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

@pytest.fixture(scope="module")
def admin_token():
    # Create an admin user
    resp = client.post("/auth/signup", json={
        "email": "admin@test.com",
        "password": "adminpass",
        "role": "admin"
    })
    assert resp.status_code == 201

    # Log in to get token
    login = client.post(
        "/auth/login",
        data={"username": "admin@test.com", "password": "adminpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def test_root():
    r = client.get("/")
    assert r.status_code == 200


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200


def test_signup_and_login_user():
    # Signup a regular user
    r1 = client.post("/auth/signup", json={
        "email": "user1@test.com",
        "password": "userpass",
        "role": "user"
    })
    assert r1.status_code == 201

    # Login the user
    r2 = client.post(
        "/auth/login",
        data={"username": "user1@test.com", "password": "userpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert r2.status_code == 200
    assert "access_token" in r2.json()


def test_create_user_as_admin(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = client.post(
        "/users/users/",
        json={"email": "user2@test.com", "password": "pass2", "role": "user"},
        headers=headers
    )
    assert r.status_code == 201
    data = r.json()
    assert data.get("email") == "user2@test.com"


def test_list_alerts():
    r = client.get("/alerts/")
    assert r.status_code == 200


def test_create_alert(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = client.post(
        "/alerts/",
        json={"message": "Test alert message"},
        headers=headers
    )
    assert r.status_code == 201


def test_debug_routes():
    r = client.get("/debug/routes")
    assert r.status_code == 200
    # ensure routes list includes create_user
    routes = [rt["path"] for rt in r.json()]
    assert "/users/users/" in routes


def test_video_feed():
    r = client.get("/video_feed")
    # this may stream or return 200/404 based on camera
    assert r.status_code in (200, 404)


def test_start_detection(admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    r = client.post("/start-detection", headers=headers)
    assert r.status_code == 200
