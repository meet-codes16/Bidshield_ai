import uuid
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.entities import Document,VerificationRecord,VerificationStatus,Role,Bid,Bidder
from app.services.hash_service import sha256_file
from app.services.authenticity_service import verify_integrity,overall_status
from app.services.providers.authority import MockAuthorityProvider,RealAuthorityProvider
from app.core.config import settings
from app.services.audit_service import log_event
router=APIRouter(prefix="/verification",tags=["verification"])

@router.post("/{document_id}")
def verify(document_id:str,user=Depends(require_roles(Role.ADMIN,Role.OFFICER,Role.AUDITOR)),db:Session=Depends(get_db)):
    d=db.get(Document,uuid.UUID(document_id))
    if not d: raise HTTPException(404,"Document not found")
    from pathlib import Path
    bid=db.get(Bid,d.bid_id)
    if user.role==Role.BIDDER:
        bidder=db.get(Bidder,bid.bidder_id) if bid else None
        if not bidder or bidder.organization_id!=user.organization_id:
            raise HTTPException(403,"Forbidden")
    path=Path(settings.UPLOAD_DIR)/f"{d.id}.pdf"
    if not path.exists(): raise HTTPException(404,"Stored document file not found")
    actual=sha256_file(str(path))
    integrity=verify_integrity(d.sha256,actual)
    provider=MockAuthorityProvider() if settings.AUTHORITY_MODE=="mock" else RealAuthorityProvider()
    authority=provider.verify("document_hash",actual)
    authority_status=VerificationStatus(authority["status"])
    overall=overall_status(integrity,authority_status)
    row=VerificationRecord(document_id=d.id,integrity_status=integrity,authority_status=authority_status,
        overall_status=overall,details={"authority":authority,"note":"Official verification is unavailable in MOCK mode."})
    db.add(row);db.commit();log_event(db,user.id,"DOCUMENT_VERIFIED","document",d.id,{"status":overall.value})
    return {"document_id":document_id,"integrity_status":integrity,"authority_status":authority_status,"overall_status":overall}
