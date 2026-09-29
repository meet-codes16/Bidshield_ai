import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.entities import Bid, BidStatus, Bidder, Tender, TenderStatus, Role, Document
from app.schemas.bid import BidCreate, DecisionRequest
from app.services.audit_service import log_event

router = APIRouter(prefix="/bids", tags=["bids"])


def _is_deadline_passed(deadline: datetime | None) -> bool:
    if not deadline:
        return False
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return deadline < datetime.now(timezone.utc)


@router.post("/tenders/{tender_id}/bids")
def create_bid(
    tender_id: str,
    data: BidCreate,
    user=Depends(require_roles(Role.BIDDER, Role.OFFICER, Role.MINISTRY_OFFICER)),
    db: Session = Depends(get_db),
):
    try:
        t_uuid = uuid.UUID(tender_id)
    except ValueError:
        raise HTTPException(400, "Invalid tender_id")

    t = db.get(Tender, t_uuid)
    if not t or t.status != TenderStatus.PUBLISHED:
        raise HTTPException(400, "Tender is not open for bidding")

    if _is_deadline_passed(t.submission_deadline):
        raise HTTPException(400, "Submission deadline has passed")

    bidder = db.scalar(select(Bidder).where(Bidder.organization_id == user.organization_id))
    if not bidder:
        raise HTTPException(400, "Bidder profile not found for your organization")
    selected_bidder = bidder

    if data.bidder_id:
        try:
            selected_bidder = db.get(Bidder, uuid.UUID(data.bidder_id))
        except ValueError:
            raise HTTPException(400, "Invalid bidder_id")
        if not selected_bidder or selected_bidder.organization_id != user.organization_id:
            raise HTTPException(403, "Bidder does not belong to your organization")

    # One Bid Per Bidder Per Tender: check existing
    existing = db.scalar(select(Bid).where(Bid.tender_id == t.id, Bid.bidder_id == selected_bidder.id))
    if existing:
        raise HTTPException(409, "You have already started or submitted a bid for this tender")

    b = Bid(tender_id=t.id, bidder_id=selected_bidder.id, status=BidStatus.DRAFT)
    try:
        db.add(b)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "You have already started or submitted a bid for this tender")

    log_event(db, user.id, "BID_STARTED", "bid", b.id, {"tender_id": str(t.id), "bidder_id": str(selected_bidder.id)})
    return {"id": str(b.id), "status": b.status}


@router.get("/tenders/{tender_id}/my-bid")
def get_my_bid_for_tender(
    tender_id: str,
    user=Depends(require_roles(Role.BIDDER)),
    db: Session = Depends(get_db),
):
    try:
        t_uuid = uuid.UUID(tender_id)
    except ValueError:
        raise HTTPException(400, "Invalid tender_id")

    bidder = db.scalar(select(Bidder).where(Bidder.organization_id == user.organization_id))
    if not bidder:
        return {"has_bid": False, "bid": None}

    bid = db.scalar(select(Bid).where(Bid.tender_id == t_uuid, Bid.bidder_id == bidder.id))
    if not bid:
        return {"has_bid": False, "bid": None}

    return {
        "has_bid": True,
        "bid": {
            "id": str(bid.id),
            "status": bid.status,
            "submitted_at": bid.submitted_at,
            "ai_recommendation": bid.ai_recommendation,
        },
    }


@router.get("")
def list_bids(
    user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.MINISTRY_OFFICER, Role.AUDITOR, Role.BIDDER)),
    db: Session = Depends(get_db),
):
    rows = db.scalars(select(Bid).order_by(Bid.submitted_at.desc().nullslast())).all()
    out = []
    for b in rows:
        if user.role == Role.BIDDER:
            bidder = db.get(Bidder, b.bidder_id)
            if not bidder or bidder.organization_id != user.organization_id:
                continue
        tender = db.get(Tender, b.tender_id)
        bidder = db.get(Bidder, b.bidder_id)
        out.append({
            "id": str(b.id),
            "tender_id": str(b.tender_id),
            "tender_number": tender.tender_number if tender else "",
            "title": tender.title if tender else "",
            "bidder_id": str(b.bidder_id),
            "bidder_name": bidder.organization_name if bidder else "",
            "status": b.status,
            "submitted_at": b.submitted_at,
            "ai_recommendation": b.ai_recommendation,
            "officer_decision": b.officer_decision,
            "officer_reason": b.officer_reason,
        })
    return out


@router.get("/{bid_id}")
def get_bid(
    bid_id: str,
    user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.MINISTRY_OFFICER, Role.AUDITOR, Role.BIDDER)),
    db: Session = Depends(get_db),
):
    try:
        bid_uuid = uuid.UUID(bid_id)
    except ValueError:
        raise HTTPException(400, "Invalid bid_id")
    b = db.get(Bid, bid_uuid)
    if not b:
        raise HTTPException(404, "Bid not found")
    if user.role == Role.BIDDER:
        bidder = db.get(Bidder, b.bidder_id)
        if not bidder or bidder.organization_id != user.organization_id:
            raise HTTPException(403, "Forbidden")
    tender = db.get(Tender, b.tender_id)
    bidder = db.get(Bidder, b.bidder_id)
    return {
        "id": str(b.id),
        "tender_id": str(b.tender_id),
        "tender_number": tender.tender_number if tender else "",
        "title": tender.title if tender else "",
        "bidder_id": str(b.bidder_id),
        "bidder_name": bidder.organization_name if bidder else "",
        "status": b.status,
        "submitted_at": b.submitted_at,
        "ai_recommendation": b.ai_recommendation,
        "officer_decision": b.officer_decision,
        "officer_reason": b.officer_reason,
    }


@router.post("/{bid_id}/submit")
def submit(
    bid_id: str,
    user=Depends(require_roles(Role.BIDDER, Role.OFFICER, Role.MINISTRY_OFFICER)),
    db: Session = Depends(get_db),
):
    try:
        bid_uuid = uuid.UUID(bid_id)
    except ValueError:
        raise HTTPException(400, "Invalid bid_id")
    b = db.get(Bid, bid_uuid)
    if not b:
        raise HTTPException(404, "Bid not found")
    bidder = db.get(Bidder, b.bidder_id)
    if not bidder:
        raise HTTPException(404, "Bidder profile not found")
    if user.role == Role.BIDDER and bidder.organization_id != user.organization_id:
        raise HTTPException(403, "Forbidden")

    # Lock check: cannot resubmit
    if b.status != BidStatus.DRAFT:
        raise HTTPException(400, "Bid has already been submitted and is locked")

    tender = db.get(Tender, b.tender_id)
    if not tender or tender.status != TenderStatus.PUBLISHED:
        raise HTTPException(400, "Tender is no longer open for submission")
    if _is_deadline_passed(tender.submission_deadline):
        raise HTTPException(400, "Submission deadline has passed")

    # Document check
    doc_count = db.scalar(select(func.count(Document.id)).where(Document.bid_id == b.id)) or 0
    if doc_count == 0:
        raise HTTPException(400, "You must upload at least one evidence document before submitting")

    # Lock and mark submitted
    b.status = BidStatus.SUBMITTED
    b.submitted_at = datetime.now(timezone.utc)
    db.commit()
    log_event(db, user.id, "BID_SUBMITTED", "bid", b.id)
    log_event(db, user.id, "BID_LOCKED", "bid", b.id)

    # Automatic pipeline: run compliance, risk, and Groq LLM analysis
    from app.api.compliance import run_bid_analysis
    try:
        run_bid_analysis(b, db, user.id)
    except Exception as pipeline_err:
        # If extraction/LLM has issues, the bid remains safely SUBMITTED and can be re-run by officer
        print("Automatic pipeline note:", pipeline_err)

    return {"id": bid_id, "status": b.status, "ai_recommendation": b.ai_recommendation}


@router.post("/{bid_id}/decision")
def decision(
    bid_id: str,
    data: DecisionRequest,
    user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.MINISTRY_OFFICER)),
    db: Session = Depends(get_db),
):
    try:
        bid_uuid = uuid.UUID(bid_id)
    except ValueError:
        raise HTTPException(400, "Invalid bid_id")
    b = db.get(Bid, bid_uuid)
    if not b:
        raise HTTPException(404, "Bid not found")
    b.officer_decision = data.decision
    b.officer_reason = data.reason
    dec = data.decision.upper()
    if dec in ("APPROVE", "ACCEPTED"):
        b.status = BidStatus.ACCEPTED
        action_name = "BID_APPROVED"
    elif dec in ("CLARIFICATION_REQUIRED", "CLARIFY"):
        b.status = BidStatus.CLARIFICATION_REQUIRED
        action_name = "BID_CLARIFICATION_REQUESTED"
    elif dec in ("REJECT", "REJECTED"):
        b.status = BidStatus.REJECTED
        action_name = "BID_REJECTED"
    else:
        b.status = BidStatus.UNDER_REVIEW
        action_name = "OFFICER_REVIEW"
    db.commit()
    log_event(db, user.id, "OFFICER_OVERRIDE", "bid", b.id, {"decision": data.decision, "reason": data.reason})
    log_event(db, user.id, action_name, "bid", b.id)
    return {
        "id": bid_id,
        "status": b.status,
        "ai_recommendation": b.ai_recommendation,
        "officer_decision": b.officer_decision,
        "officer_reason": b.officer_reason,
    }
