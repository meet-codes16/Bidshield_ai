import uuid
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.entities import Tender,Requirement,Bid,TenderStatus,Role
from app.schemas.tender import TenderCreate,RequirementCreate
from app.services.audit_service import log_event
router=APIRouter(prefix="/tenders",tags=["tenders"])

@router.post("")
def create(data:TenderCreate,user=Depends(require_roles(Role.ADMIN,Role.OFFICER)),db:Session=Depends(get_db)):
    t=Tender(**data.model_dump(),created_by=user.id); db.add(t); db.commit()
    log_event(db,user.id,"TENDER_CREATED","tender",t.id,{"tender_number":t.tender_number})
    return {"id":str(t.id),"tender_number":t.tender_number,"title":t.title,"status":t.status}

@router.get("")
def list_tenders(user=Depends(require_roles(Role.ADMIN,Role.OFFICER,Role.AUDITOR,Role.BIDDER)),db:Session=Depends(get_db)):
    rows=db.scalars(select(Tender).order_by(Tender.created_at.desc())).all()
    out = []
    for t in rows:
        bid_count = db.scalar(select(func.count(Bid.id)).where(Bid.tender_id == t.id)) or 0
        out.append({"id":str(t.id),"tender_number":t.tender_number,"title":t.title,"description":t.description,
                    "department":t.department,"category":t.category,"estimated_value":t.estimated_value,
                    "publish_date":t.publish_date,"submission_deadline":t.submission_deadline,
                    "status":t.status,"bid_count":bid_count})
    return out

@router.post("/{tender_id}/publish")
def publish(tender_id:str,user=Depends(require_roles(Role.ADMIN,Role.OFFICER)),db:Session=Depends(get_db)):
    t=db.get(Tender,uuid.UUID(tender_id))
    if not t: raise HTTPException(404,"Tender not found")
    t.status=TenderStatus.PUBLISHED; db.commit(); log_event(db,user.id,"TENDER_PUBLISHED","tender",t.id)
    return {"id":tender_id,"status":t.status}

@router.post("/{tender_id}/requirements")
def add_requirement(tender_id:str,data:RequirementCreate,user=Depends(require_roles(Role.ADMIN,Role.OFFICER)),db:Session=Depends(get_db)):
    t=db.get(Tender,uuid.UUID(tender_id))
    if not t: raise HTTPException(404,"Tender not found")
    r=Requirement(tender_id=t.id,**data.model_dump()); db.add(r); db.commit()
    log_event(db,user.id,"REQUIREMENT_CREATED","requirement",r.id,{"tender_id":tender_id})
    return {"id":str(r.id),**data.model_dump()}

@router.get("/{tender_id}")
def get_tender(tender_id:str,user=Depends(require_roles(Role.ADMIN,Role.OFFICER,Role.AUDITOR,Role.BIDDER)),db:Session=Depends(get_db)):
    try:
        tid = uuid.UUID(tender_id)
    except ValueError:
        raise HTTPException(400, "Invalid tender_id")
    t = db.get(Tender, tid)
    if not t:
        raise HTTPException(404, "Tender not found")
    bid_count = db.scalar(select(func.count(Bid.id)).where(Bid.tender_id == t.id)) or 0
    reqs = db.scalars(select(Requirement).where(Requirement.tender_id == t.id)).all()
    return {
        "id": str(t.id),
        "tender_number": t.tender_number,
        "title": t.title,
        "description": t.description,
        "department": t.department,
        "category": t.category,
        "estimated_value": t.estimated_value,
        "publish_date": t.publish_date,
        "submission_deadline": t.submission_deadline,
        "status": t.status,
        "bid_count": bid_count,
        "requirements": [
            {
                "id": str(r.id),
                "requirement_text": r.requirement_text,
                "mandatory": r.mandatory,
                "weight": r.weight,
                "category": r.category,
            }
            for r in reqs
        ]
    }

@router.get("/{tender_id}/requirements")
def requirements(tender_id:str,user=Depends(require_roles(Role.ADMIN,Role.OFFICER,Role.AUDITOR,Role.BIDDER)),db:Session=Depends(get_db)):
    rows=db.scalars(select(Requirement).where(Requirement.tender_id==uuid.UUID(tender_id))).all()
    return [{"id":str(r.id),"requirement_text":r.requirement_text,"mandatory":r.mandatory,"weight":r.weight} for r in rows]
