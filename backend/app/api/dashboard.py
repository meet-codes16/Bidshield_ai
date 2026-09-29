from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.entities import *

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

def _tender_stats(db, tender):
    bid_count = db.scalar(select(func.count(Bid.id)).where(Bid.tender_id == tender.id)) or 0
    submitted = db.scalar(select(func.count(Bid.id)).where(Bid.tender_id == tender.id, Bid.status.in_([BidStatus.SUBMITTED, BidStatus.UNDER_REVIEW, BidStatus.COMPLIANT, BidStatus.ACCEPTED, BidStatus.REJECTED]))) or 0
    return bid_count, submitted

@router.get("/summary")
def summary(user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.AUDITOR, Role.BIDDER)), db: Session = Depends(get_db)):
    if user.role == Role.BIDDER:
        bidder = db.scalar(select(Bidder).where(Bidder.organization_id == user.organization_id))
        my_bids = db.scalar(select(func.count(Bid.id)).where(Bid.bidder_id == bidder.id)) if bidder else 0
        published = db.scalar(select(func.count(Tender.id)).where(Tender.status == TenderStatus.PUBLISHED)) or 0
        return {
            "active_tenders": published,
            "my_bids": my_bids or 0,
            "submitted_bids": db.scalar(select(func.count(Bid.id)).where(Bid.bidder_id == bidder.id, Bid.status != BidStatus.DRAFT)) if bidder else 0,
            "documents": db.scalar(select(func.count(Document.id)).join(Bid, Document.bid_id == Bid.id).where(Bid.bidder_id == bidder.id)) if bidder else 0,
        }

    return {
        "active_tenders": db.scalar(select(func.count(Tender.id)).where(Tender.status == TenderStatus.PUBLISHED)) or 0,
        "bids_received": db.scalar(select(func.count(Bid.id)).where(Bid.status != BidStatus.DRAFT)) or 0,
        "pending_reviews": db.scalar(select(func.count(Bid.id)).where(Bid.status == BidStatus.UNDER_REVIEW)) or 0,
        "high_risk_bids": db.scalar(select(func.count(RiskAssessment.id)).where(RiskAssessment.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]))) or 0,
        "total_tenders": db.scalar(select(func.count(Tender.id))) or 0,
        "award_value": db.scalar(select(func.coalesce(func.sum(Tender.estimated_value), 0)).where(Tender.status == TenderStatus.AWARDED)) or 0,
    }

@router.get("/analytics")
def analytics(user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.AUDITOR, Role.BIDDER)), db: Session = Depends(get_db)):
    tenders = db.scalars(select(Tender).order_by(Tender.created_at.desc())).all()
    tender_rows = []
    for t in tenders:
        count, submitted = _tender_stats(db, t)
        scores = db.scalars(select(ComplianceResult).join(Bid, ComplianceResult.bid_id == Bid.id).where(Bid.tender_id == t.id)).all()
        avg_score = round(sum(float(x.confidence or 0) for x in scores) / len(scores) * 100, 1) if scores else None
        tender_rows.append({
            "id": str(t.id), "tender_number": t.tender_number, "title": t.title,
            "status": t.status.value, "department": t.department or "",
            "estimated_value": t.estimated_value or 0, "deadline": t.submission_deadline.isoformat() if t.submission_deadline else None,
            "bids": count, "submitted_bids": submitted, "avg_confidence": avg_score,
        })

    bids = db.scalars(select(Bid).order_by(Bid.submitted_at.desc().nullslast())).all()
    status_counts = {}
    for b in bids:
        status_counts[b.status.value] = status_counts.get(b.status.value, 0) + 1

    return {"tenders": tender_rows, "bid_status": status_counts, "generated_at": datetime.now(timezone.utc).isoformat()}


@router.get("/bidders")
def bidders(user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.MINISTRY_OFFICER, Role.AUDITOR, Role.BIDDER)), db: Session = Depends(get_db)):
    rows = db.scalars(select(Bidder).order_by(Bidder.organization_name.asc())).all()
    out = []
    for b in rows:
        total = db.scalar(select(func.count(Bid.id)).where(Bid.bidder_id == b.id)) or 0
        submitted = db.scalar(select(func.count(Bid.id)).where(Bid.bidder_id == b.id, Bid.status != BidStatus.DRAFT)) or 0
        out.append({"id": str(b.id), "name": b.organization_name, "gstin": b.gstin,
                    "registration_number": b.registration_number, "verification_status": b.verification_status.value,
                    "bids": total, "submitted": submitted})
    return out
