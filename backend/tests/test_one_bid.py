import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.main import app, _ensure_demo_data
from app.core.database import Base, engine, SessionLocal
from app.models.entities import Tender, Bid, Bidder, TenderStatus, BidStatus

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    _ensure_demo_data()

def get_auth_token(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]

def test_first_bid_succeeds_and_duplicate_bid_returns_409():
    client = TestClient(app)
    # Log in as bidder 10
    token = get_auth_token(client, "bidder10@bidshield.demo", "Bidder@10")
    headers = {"Authorization": f"Bearer {token}"}

    # Find a tender with no existing bid for bidder 10
    tenders_res = client.get("/api/tenders", headers=headers)
    assert tenders_res.status_code == 200
    tenders = [t for t in tenders_res.json() if t["status"] == "PUBLISHED"]
    assert len(tenders) > 0

    target_tender = None
    for t in tenders:
        my_bid_res = client.get(f"/api/bids/tenders/{t['id']}/my-bid", headers=headers)
        if my_bid_res.status_code == 200 and not my_bid_res.json().get("has_bid"):
            target_tender = t
            break

    assert target_tender is not None, "Should find at least one open tender without a bid"
    tender_id = target_tender["id"]

    # 1. First bid creation succeeds
    sub_res = client.post(f"/api/bids/tenders/{tender_id}/bids", json={}, headers=headers)
    assert sub_res.status_code in [200, 201], sub_res.text
    sub_data = sub_res.json()
    assert "id" in sub_data
    assert sub_data["status"] == "DRAFT"

    # 2. Check my-bid reflects the new bid
    my_bid_res2 = client.get(f"/api/bids/tenders/{tender_id}/my-bid", headers=headers)
    assert my_bid_res2.status_code == 200
    assert my_bid_res2.json().get("has_bid") is True
    assert my_bid_res2.json()["bid"]["id"] == sub_data["id"]

    # 3. Duplicate bid on same tender by same bidder MUST return 409 Conflict
    dup_res = client.post(f"/api/bids/tenders/{tender_id}/bids", json={}, headers=headers)
    assert dup_res.status_code == 409
    assert "already" in dup_res.json()["detail"].lower()

def test_database_level_unique_constraint():
    db = SessionLocal()
    try:
        tenders = db.scalars(select(Tender)).all()
        bidders = db.scalars(select(Bidder)).all()
        assert len(tenders) > 0 and len(bidders) > 0

        t = tenders[0]
        b = bidders[0]

        # Ensure at least one bid exists
        existing = db.scalar(select(Bid).where(Bid.tender_id == t.id, Bid.bidder_id == b.id))
        if not existing:
            first_bid = Bid(tender_id=t.id, bidder_id=b.id, status=BidStatus.SUBMITTED)
            db.add(first_bid)
            db.commit()

        # Attempting direct duplicate insert must fail with IntegrityError
        with pytest.raises(IntegrityError):
            duplicate_bid = Bid(tender_id=t.id, bidder_id=b.id, status=BidStatus.SUBMITTED)
            db.add(duplicate_bid)
            db.commit()
    finally:
        db.rollback()
        db.close()

def test_submission_to_expired_tender_rejected():
    client = TestClient(app)
    # Log in as officer to create an expired tender
    officer_token = get_auth_token(client, "officer.mp@bidshield.demo", "Demo@MP2026")
    off_headers = {"Authorization": f"Bearer {officer_token}"}

    db = SessionLocal()
    try:
        # Create an expired tender directly or check for CLOSED
        expired_tender = db.scalar(select(Tender).where(Tender.status == TenderStatus.CLOSED))
        assert expired_tender is not None, "Expired demo tender should exist"
        expired_id = str(expired_tender.id)
    finally:
        db.close()

    # Log in as bidder 09
    bidder_token = get_auth_token(client, "bidder09@bidshield.demo", "Bidder@09")
    bid_headers = {"Authorization": f"Bearer {bidder_token}"}

    # Attempting to submit bid to closed/expired tender must return 400
    res = client.post(f"/api/bids/tenders/{expired_id}/bids", json={}, headers=bid_headers)
    assert res.status_code == 400
    assert "deadline" in res.json()["detail"].lower() or "not open" in res.json()["detail"].lower()
