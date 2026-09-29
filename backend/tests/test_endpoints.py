import pytest
from fastapi.testclient import TestClient
from app.main import app, _ensure_demo_data
from app.core.database import Base, engine

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    _ensure_demo_data()

def get_auth_token(client, email="officer@bidshield.ai", password="BidShield@2026"):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]

def test_get_tender_by_id():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List tenders
    res = client.get("/api/tenders", headers=headers)
    assert res.status_code == 200
    tenders = res.json()
    assert len(tenders) > 0
    tender_id = tenders[0]["id"]

    # 2. Get single tender by id
    single = client.get(f"/api/tenders/{tender_id}", headers=headers)
    assert single.status_code == 200
    data = single.json()
    assert data["id"] == tender_id
    assert "requirements" in data
    assert isinstance(data["requirements"], list)

def test_bid_decision_clarification_required():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get bids
    res = client.get("/api/bids", headers=headers)
    assert res.status_code == 200
    bids = res.json()
    assert len(bids) > 0
    bid_id = bids[0]["id"]

    # 2. Decision: CLARIFICATION_REQUIRED
    dec_res = client.post(f"/api/bids/{bid_id}/decision", json={
        "decision": "CLARIFICATION_REQUIRED",
        "reason": "Please provide updated GST filing certificate."
    }, headers=headers)
    assert dec_res.status_code == 200, dec_res.text
    assert dec_res.json()["status"] == "CLARIFICATION_REQUIRED"

def test_bid_decision_approve():
    client = TestClient(app)
    token = get_auth_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/bids", headers=headers)
    assert res.status_code == 200
    bids = res.json()
    bid_id = bids[0]["id"]

    dec_res = client.post(f"/api/bids/{bid_id}/decision", json={
        "decision": "APPROVE",
        "reason": "All evidence verified."
    }, headers=headers)
    assert dec_res.status_code == 200, dec_res.text
    assert dec_res.json()["status"] == "ACCEPTED"
