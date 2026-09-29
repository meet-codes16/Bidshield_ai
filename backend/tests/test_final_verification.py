import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app, _ensure_demo_data
from app.core.database import Base, engine, SessionLocal
from app.models.entities import (
    User, Tender, Bid, Document, AIAnalysis, AuditLog, Bidder,
    Role, TenderStatus, BidStatus, ComplianceStatus, RiskLevel
)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    _ensure_demo_data()

def login(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_01_all_15_demo_presets_and_aliases():
    client = TestClient(app)
    # 5 Officers
    officers = [
        ("officer.mp@bidshield.demo", "Demo@MP2026", "MINISTRY_OFFICER", "Madhya Pradesh"),
        ("officer.rajasthan@bidshield.demo", "Demo@RJ2026", "MINISTRY_OFFICER", "Rajasthan"),
        ("officer.maharashtra@bidshield.demo", "Demo@MH2026", "MINISTRY_OFFICER", "Maharashtra"),
        ("officer.gujarat@bidshield.demo", "Demo@GJ2026", "MINISTRY_OFFICER", "Gujarat"),
        ("officer.up@bidshield.demo", "Demo@UP2026", "MINISTRY_OFFICER", "Uttar Pradesh"),
    ]
    for email, pwd, expected_role, expected_org_fragment in officers:
        token = login(client, email, pwd)
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        assert me["role"] in ["OFFICER", "MINISTRY_OFFICER"]
        assert expected_org_fragment in me["organization_name"]

    # 10 Bidders
    bidders = [
        ("bidder01@bidshield.demo", "Bidder@01", "Apex InfraTech"),
        ("bidder02@bidshield.demo", "Bidder@02", "Bharat Digital Systems"),
        ("bidder03@bidshield.demo", "Bidder@03", "NexGen Solutions"),
        ("bidder04@bidshield.demo", "Bidder@04", "Vertex Engineering"),
        ("bidder05@bidshield.demo", "Bidder@05", "BluePeak Technologies"),
        ("bidder06@bidshield.demo", "Bidder@06", "Arvind Infrastructure"),
        ("bidder07@bidshield.demo", "Bidder@07", "TechBridge Systems"),
        ("bidder08@bidshield.demo", "Bidder@08", "Suryodaya Engineering"),
        ("bidder09@bidshield.demo", "Bidder@09", "Innovexa Digital"),
        ("bidder10@bidshield.demo", "Bidder@10", "PrimeGrid Technologies"),
    ]
    for email, pwd, expected_org_fragment in bidders:
        token = login(client, email, pwd)
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
        assert me["role"] == "BIDDER"
        assert expected_org_fragment in me["organization_name"]

def test_02_live_groq_execution_and_ai_persistence():
    client = TestClient(app)
    off_token = login(client, "officer.maharashtra@bidshield.demo", "Demo@MH2026")
    headers = {"Authorization": f"Bearer {off_token}"}

    # Find a bid that has documents attached
    db = SessionLocal()
    try:
        doc = db.scalars(select(Document)).first()
        assert doc is not None, "A seeded document should exist"
        target_bid_id = str(doc.bid_id)
    finally:
        db.close()

    # Call POST /api/compliance/bids/{bid_id}/analyze
    res = client.post(f"/api/compliance/bids/{target_bid_id}/analyze", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()

    assert "overall_compliance_score" in data
    assert "risk" in data
    assert "ai_recommendation" in data
    assert "ai_analysis" in data
    assert len(data.get("requirements", [])) > 0

    # Verify persistence in ai_analyses table
    db = SessionLocal()
    try:
        stored_ai = db.scalars(select(AIAnalysis).where(AIAnalysis.bid_id == uuid.UUID(target_bid_id)).order_by(AIAnalysis.created_at.desc())).first()
        assert stored_ai is not None, "AI analysis must be persisted in database"
        assert stored_ai.overall_assessment is not None
        assert stored_ai.model_name == "openai/gpt-oss-20b"
    finally:
        db.close()

    # Verify cached retrieval via GET /api/compliance/bids/{bid_id}/result
    cached_res = client.get(f"/api/compliance/bids/{target_bid_id}/result", headers=headers)
    assert cached_res.status_code == 200
    cached_data = cached_res.json()
    assert cached_data["status"] == "ANALYZED"
    assert cached_data["ai_analysis"]["model_name"] == "openai/gpt-oss-20b"

def test_03_one_bid_locking_and_immutability():
    client = TestClient(app)
    bidder_token = login(client, "bidder07@bidshield.demo", "Bidder@07")
    b_headers = {"Authorization": f"Bearer {bidder_token}"}

    # Find a published tender without a bid for bidder 07
    tenders = client.get("/api/tenders", headers=b_headers).json()
    open_tenders = [t for t in tenders if t["status"] == "PUBLISHED"]
    assert len(open_tenders) > 0

    target_tender = None
    for t in open_tenders:
        mb = client.get(f"/api/bids/tenders/{t['id']}/my-bid", headers=b_headers).json()
        if not mb.get("has_bid"):
            target_tender = t
            break

    assert target_tender is not None
    tender_id = target_tender["id"]

    # 1. Create Draft Bid
    b_res = client.post(f"/api/bids/tenders/{tender_id}/bids", json={}, headers=b_headers)
    assert b_res.status_code == 200
    bid_id = b_res.json()["id"]

    # 2. Second bid attempt on same tender -> 409 Conflict
    dup_res = client.post(f"/api/bids/tenders/{tender_id}/bids", json={}, headers=b_headers)
    assert dup_res.status_code == 409

    # 3. Cannot submit without documents -> 400
    sub_err = client.post(f"/api/bids/{bid_id}/submit", headers=b_headers)
    assert sub_err.status_code == 400
    assert "upload at least one" in sub_err.json()["detail"].lower()

def test_04_role_isolation_and_authorization():
    client = TestClient(app)
    b1_token = login(client, "bidder01@bidshield.demo", "Bidder@01")
    b2_token = login(client, "bidder02@bidshield.demo", "Bidder@02")
    off_token = login(client, "officer.mp@bidshield.demo", "Demo@MP2026")

    b1_headers = {"Authorization": f"Bearer {b1_token}"}
    b2_headers = {"Authorization": f"Bearer {b2_token}"}
    off_headers = {"Authorization": f"Bearer {off_token}"}

    # Find a bid belonging to Bidder 01
    b1_bids = client.get("/api/bids", headers=b1_headers).json()
    assert len(b1_bids) > 0
    b1_bid_id = b1_bids[0]["id"]

    # Bidder 02 attempting to view Bidder 01's bid must be rejected with 403
    forbidden_view = client.get(f"/api/bids/{b1_bid_id}", headers=b2_headers)
    assert forbidden_view.status_code == 403

    # Bidder 01 attempting to make officer decision must be rejected with 403
    forbidden_dec = client.post(f"/api/bids/{b1_bid_id}/decision", json={"decision": "APPROVE", "reason": "Self-approval"}, headers=b1_headers)
    assert forbidden_dec.status_code == 403

    # Bidder 01 attempting to run compliance analysis directly must be rejected with 403
    forbidden_ana = client.post(f"/api/compliance/bids/{b1_bid_id}/analyze", headers=b1_headers)
    assert forbidden_ana.status_code == 403

    # Bidder 01 attempting to access full audit logs must be rejected with 403
    forbidden_aud = client.get("/api/audit", headers=b1_headers)
    assert forbidden_aud.status_code == 403

    # Officer CAN access all these endpoints
    allowed_view = client.get(f"/api/bids/{b1_bid_id}", headers=off_headers)
    assert allowed_view.status_code == 200

    allowed_aud = client.get("/api/audit", headers=off_headers)
    assert allowed_aud.status_code == 200

def test_05_audit_hash_chain_integrity():
    client = TestClient(app)
    off_token = login(client, "officer.maharashtra@bidshield.demo", "Demo@MH2026")
    headers = {"Authorization": f"Bearer {off_token}"}

    res = client.get("/api/audit", headers=headers)
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 10, "Should have sufficient audit events"

    # API returns ordered by timestamp.desc()
    # For every event i (newer), its previous_hash should match event i+1's current_hash
    # where event i+1 is the chronologically preceding event
    for i in range(len(events) - 1):
        newer = events[i]
        older = events[i + 1]
        assert newer["previous_hash"] == older["current_hash"], (
            f"Broken hash chain between event {newer['id']} and {older['id']}"
        )
