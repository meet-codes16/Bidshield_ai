import pytest
from fastapi.testclient import TestClient
from app.main import app, _ensure_demo_data
from app.core.database import Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    _ensure_demo_data()

def test_auth_login_and_me():
    client = TestClient(app)
    # 1. Login with demo officer
    res = client.post("/api/auth/login", json={
        "email": "officer@bidshield.ai",
        "password": "BidShield@2026"
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["role"] in ["OFFICER", "MINISTRY_OFFICER"]
    assert "Maharashtra" in data["user"]["organization_name"]

    # 2. Call /api/auth/me with the access token
    token = data["access_token"]
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200, me_res.text
    me_data = me_res.json()
    assert me_data["email"] == "officer@bidshield.ai"
    assert me_data["full_name"] == "Priya Sharma"

def test_auth_login_invalid_credentials():
    client = TestClient(app)
    res = client.post("/api/auth/login", json={
        "email": "officer@bidshield.ai",
        "password": "WrongPassword123"
    })
    assert res.status_code == 401
