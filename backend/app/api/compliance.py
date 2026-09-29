import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.entities import (
    Bid, Requirement, Document, ComplianceResult, Evidence, RiskAssessment,
    ComplianceStatus, BidStatus, Role, VerificationRecord, VerificationStatus, AIAnalysis
)
from app.services.document_service import extract_pdf_pages, chunk_pages
from app.services.rag_service import RAGService
from app.services.providers.llm import get_llm_provider
from app.services.compliance_service import ComplianceEngine
from app.services.risk_service import calculate_risk
from app.services.audit_service import log_event

router = APIRouter(prefix="/compliance", tags=["compliance"])


def run_bid_analysis(bid: Bid, db: Session, user_id=None):
    reqs = db.scalars(select(Requirement).where(Requirement.tender_id == bid.tender_id)).all()
    if not reqs:
        raise HTTPException(400, "Tender has no requirements")
    docs = db.scalars(select(Document).where(Document.bid_id == bid.id)).all()
    if not docs:
        raise HTTPException(400, "No bidder documents available")

    all_chunks = []
    for d in docs:
        path = Path(settings.UPLOAD_DIR) / f"{d.id}.pdf"
        if not path.exists():
            continue
        try:
            pages = extract_pdf_pages(str(path))
            if not any(p.get("text", "").strip() for p in pages):
                from app.services.ocr_service import ocr_pdf
                pages = ocr_pdf(str(path))
        except Exception:
            pages = []
        for c in chunk_pages(pages):
            all_chunks.append({
                "document_id": str(d.id),
                "page": c["page"],
                "text": c["text"],
                "bidder_id": str(bid.bidder_id),
                "tender_id": str(bid.tender_id),
            })
    if not all_chunks:
        raise HTTPException(422, "No text could be extracted from bidder documents")

    rag = RAGService()
    evidence_by_req = {}
    for r in reqs:
        evidence_by_req[str(r.id)] = rag.retrieve(r.requirement_text, all_chunks, top_k=3)

    ai_error = None
    try:
        llm_result = get_llm_provider().analyze(reqs, evidence_by_req)
    except Exception as exc:
        ai_error = str(exc)
        llm_result = {
            "overall_assessment": f"AI analysis unavailable: {ai_error}",
            "key_strengths": [],
            "key_concerns": ["AI analysis failed; falling back to deterministic rule checks."],
            "clarifications_required": [],
            "requirements": [],
        }

    # Clean old results
    old_results = db.scalars(select(ComplianceResult).where(ComplianceResult.bid_id == bid.id)).all()
    for old in old_results:
        db.execute(delete(Evidence).where(Evidence.compliance_result_id == old.id))
        db.delete(old)
    old_risk = db.scalar(select(RiskAssessment).where(RiskAssessment.bid_id == bid.id))
    if old_risk:
        db.delete(old_risk)
    old_ai = db.scalar(select(AIAnalysis).where(AIAnalysis.bid_id == bid.id))
    if old_ai:
        db.delete(old_ai)
    db.flush()

    engine = ComplianceEngine()
    results, overall, mandatory = engine.evaluate(reqs, llm_result.get("requirements", []), evidence_by_req)
    for r, status, conf, expl in results:
        cr = ComplianceResult(
            bid_id=bid.id, requirement_id=r.id, status=status, confidence=conf,
            explanation=expl, ai_recommendation=status.value
        )
        db.add(cr)
        db.flush()
        for e in evidence_by_req.get(str(r.id), [])[:2]:
            db.add(Evidence(
                compliance_result_id=cr.id,
                document_id=uuid.UUID(e["document_id"]),
                page_number=e["page"], text=e["text"], relevance_score=e.get("score", 0)
            ))

    missing = sum(1 for r, s, _, _ in results if r.mandatory and s != ComplianceStatus.PASS)
    authenticity_review = False
    for d in docs:
        vr = db.scalar(select(VerificationRecord).where(VerificationRecord.document_id == d.id).order_by(VerificationRecord.created_at.desc()))
        if vr and vr.overall_status in {VerificationStatus.FAILED, VerificationStatus.REVIEW, VerificationStatus.UNAVAILABLE}:
            authenticity_review = True
            break
    low_confidence = any(c < 0.5 for _, _, c, _ in results)
    risk_score, risk_level, factors = calculate_risk(overall, missing, authenticity_review, 0, low_confidence)
    db.add(RiskAssessment(bid_id=bid.id, risk_score=risk_score, risk_level=risk_level, factors=factors))

    ai_record = AIAnalysis(
        bid_id=bid.id,
        overall_assessment=llm_result.get("overall_assessment") or "AI compliance analysis completed.",
        key_strengths=llm_result.get("key_strengths", []),
        key_concerns=llm_result.get("key_concerns", []),
        clarifications_required=llm_result.get("clarifications_required", []),
        recommendation_context=llm_result.get("recommendation_context"),
        raw_response=llm_result,
        model_name=settings.GROQ_MODEL if not ai_error else "unavailable",
    )
    db.add(ai_record)

    bid.ai_recommendation = "PASS" if overall >= 80 and missing == 0 else "REVIEW"
    bid.status = BidStatus.UNDER_REVIEW
    db.commit()

    action = "AI_ANALYSIS_COMPLETED" if not ai_error else "AI_ANALYSIS_FAILED"
    log_event(db, user_id, action, "bid", bid.id, {"compliance_score": overall, "risk": risk_level.value, "error": ai_error})

    return {
        "bid_id": str(bid.id),
        "mandatory_compliance_score": mandatory,
        "overall_compliance_score": overall,
        "ai_recommendation": bid.ai_recommendation,
        "risk": {"score": risk_score, "level": risk_level.value if hasattr(risk_level, 'value') else str(risk_level)},
        "ai_analysis": {
            "overall_assessment": ai_record.overall_assessment,
            "key_strengths": ai_record.key_strengths,
            "key_concerns": ai_record.key_concerns,
            "clarifications_required": ai_record.clarifications_required,
            "model_name": ai_record.model_name,
        },
        "requirements": [
            {
                "requirement_id": str(r.id),
                "requirement": r.requirement_text,
                "status": s.value if hasattr(s, "value") else str(s),
                "confidence": c,
                "explanation": x,
                "evidence": [
                    {"document_id": e["document_id"], "page": e["page"], "text": e["text"]}
                    for e in evidence_by_req.get(str(r.id), [])[:2]
                ]
            }
            for r, s, c, x in results
        ]
    }


@router.post("/bids/{bid_id}/analyze")
def analyze(
    bid_id: str,
    user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.MINISTRY_OFFICER)),
    db: Session = Depends(get_db),
):
    try:
        bid = db.get(Bid, uuid.UUID(bid_id))
    except ValueError:
        raise HTTPException(400, "Invalid bid_id")
    if not bid:
        raise HTTPException(404, "Bid not found")
    return run_bid_analysis(bid, db, user.id)


@router.get("/bids/{bid_id}/result")
def get_analysis_result(
    bid_id: str,
    user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.MINISTRY_OFFICER, Role.AUDITOR, Role.BIDDER)),
    db: Session = Depends(get_db),
):
    try:
        bid = db.get(Bid, uuid.UUID(bid_id))
    except ValueError:
        raise HTTPException(400, "Invalid bid_id")
    if not bid:
        raise HTTPException(404, "Bid not found")
    if user.role == Role.BIDDER:
        from app.models.entities import Bidder
        bidder = db.get(Bidder, bid.bidder_id)
        if not bidder or bidder.organization_id != user.organization_id:
            raise HTTPException(403, "Forbidden")

    results = db.scalars(select(ComplianceResult).where(ComplianceResult.bid_id == bid.id)).all()
    if not results:
        return {"bid_id": bid_id, "status": "NOT_ANALYZED", "requirements": []}

    req_map = {r.id: r for r in db.scalars(select(Requirement).where(Requirement.tender_id == bid.tender_id)).all()}
    risk = db.scalar(select(RiskAssessment).where(RiskAssessment.bid_id == bid.id))
    ai_record = db.scalar(select(AIAnalysis).where(AIAnalysis.bid_id == bid.id))

    passed = sum(req_map[r.requirement_id].weight for r in results if r.requirement_id in req_map and r.status == ComplianceStatus.PASS)
    total_w = sum(req_map[r.requirement_id].weight for r in results if r.requirement_id in req_map) or 1
    mandatory_reqs = [r for r in results if r.requirement_id in req_map and req_map[r.requirement_id].mandatory]
    mandatory_p = sum(req_map[r.requirement_id].weight for r in mandatory_reqs if r.status == ComplianceStatus.PASS)
    mandatory_tot = sum(req_map[r.requirement_id].weight for r in mandatory_reqs) or 1

    overall = round(100 * passed / total_w, 2)
    mandatory_score = round(100 * mandatory_p / mandatory_tot, 2)

    req_list = []
    for cr in results:
        r_obj = req_map.get(cr.requirement_id)
        evs = db.scalars(select(Evidence).where(Evidence.compliance_result_id == cr.id)).all()
        req_list.append({
            "requirement_id": str(cr.requirement_id),
            "requirement": r_obj.requirement_text if r_obj else "",
            "status": cr.status.value if hasattr(cr.status, "value") else str(cr.status),
            "confidence": cr.confidence,
            "explanation": cr.explanation,
            "evidence": [{"document_id": str(e.document_id), "page": e.page_number, "text": e.text} for e in evs]
        })

    return {
        "bid_id": str(bid.id),
        "status": "ANALYZED",
        "mandatory_compliance_score": mandatory_score,
        "overall_compliance_score": overall,
        "ai_recommendation": bid.ai_recommendation,
        "risk": {
            "score": risk.risk_score if risk else 0,
            "level": (risk.risk_level.value if hasattr(risk.risk_level, 'value') else str(risk.risk_level)) if risk else "LOW"
        },
        "ai_analysis": {
            "overall_assessment": ai_record.overall_assessment if ai_record else "No summary available.",
            "key_strengths": ai_record.key_strengths if ai_record else [],
            "key_concerns": ai_record.key_concerns if ai_record else [],
            "clarifications_required": ai_record.clarifications_required if ai_record else [],
            "model_name": ai_record.model_name if ai_record else "",
        },
        "requirements": req_list,
    }
