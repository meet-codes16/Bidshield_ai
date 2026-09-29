import uuid, mimetypes
from pathlib import Path
from fastapi import APIRouter,Depends,HTTPException,UploadFile,File
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.entities import Bid,Document,DocumentVersion,Role,ProcessingJob,ProcessingStatus
from app.services.hash_service import sha256_file
from app.services.document_service import is_valid_pdf,extract_pdf_pages,save_extracted,chunk_pages
from app.services.storage_service import storage_provider
from app.services.audit_service import log_event
router=APIRouter(prefix="/documents",tags=["documents"])

@router.post("/bids/{bid_id}/upload")
async def upload(bid_id:str,file:UploadFile=File(...),user=Depends(require_roles(Role.BIDDER,Role.OFFICER)),db:Session=Depends(get_db)):
    bid=db.get(Bid,uuid.UUID(bid_id))
    if not bid: raise HTTPException(404,"Bid not found")
    if user.role==Role.BIDDER:
        from app.models.entities import Bidder
        bidder=db.get(Bidder,bid.bidder_id)
        if not bidder or bidder.organization_id!=user.organization_id: raise HTTPException(403,"Forbidden")
    if file.content_type!="application/pdf": raise HTTPException(400,"PDF files only")
    content=await file.read()
    if len(content)>settings.MAX_UPLOAD_SIZE: raise HTTPException(413,"File too large")
    if not is_valid_pdf(content): raise HTTPException(400,"Invalid PDF")
    doc_id=uuid.uuid4(); key=f"{bid.tender_id}/{bid.bidder_id}/{doc_id}.pdf"
    storage_provider.put(key,content)
    tmp=Path(settings.UPLOAD_DIR);tmp.mkdir(parents=True,exist_ok=True);path=tmp/f"{doc_id}.pdf";path.write_bytes(content)
    h=sha256_file(str(path))
    d=Document(id=doc_id,bid_id=bid.id,original_filename=file.filename or "document.pdf",mime_type="application/pdf",file_size=len(content),sha256=h,storage_key=key)
    db.add(d);db.add(DocumentVersion(document_id=doc_id,version_number=1,sha256=h,storage_key=key))
    job=ProcessingJob(job_type="process_document",entity_id=str(doc_id));db.add(job);db.commit()
    log_event(db,user.id,"DOCUMENT_UPLOADED","document",doc_id,{"sha256":h})
    return {"document_id":str(doc_id),"sha256":h,"job_id":str(job.id),"status":"QUEUED"}

@router.post("/{document_id}/process")
def process(document_id:str,user=Depends(require_roles(Role.ADMIN,Role.OFFICER,Role.BIDDER)),db:Session=Depends(get_db)):
    d=db.get(Document,uuid.UUID(document_id))
    if not d: raise HTTPException(404,"Document not found")
    bid=db.get(Bid,d.bid_id)
    if not bid: raise HTTPException(404,"Bid not found")
    if user.role==Role.BIDDER:
        from app.models.entities import Bidder
        bidder=db.get(Bidder,bid.bidder_id)
        if not bidder or bidder.organization_id!=user.organization_id:
            raise HTTPException(403,"Forbidden")
    path=Path(settings.UPLOAD_DIR)/f"{d.id}.pdf"
    if not path.exists():
        raise HTTPException(404,"Stored document file not found")
    d.status="PROCESSING"
    db.commit()
    try:
        pages=extract_pdf_pages(str(path))
        if not any(p["text"] for p in pages):
            from app.services.ocr_service import ocr_pdf
            pages=ocr_pdf(str(path))
        if not any(p.get("text","").strip() for p in pages):
            raise RuntimeError("No text could be extracted from the PDF")
        save_extracted(d.id,pages)
        d.status="PROCESSED"
        jobs=db.scalars(select(ProcessingJob).where(ProcessingJob.entity_id==str(d.id), ProcessingJob.job_type=="process_document").order_by(ProcessingJob.created_at.desc())).all()
        for job in jobs:
            job.status=ProcessingStatus.COMPLETED
            job.progress=100
            job.error=None
        db.commit()
        return {"document_id":document_id,"pages":len(pages),"chunks":len(chunk_pages(pages)),"status":"PROCESSED"}
    except Exception as exc:
        d.status="FAILED"
        jobs=db.scalars(select(ProcessingJob).where(ProcessingJob.entity_id==str(d.id), ProcessingJob.job_type=="process_document").order_by(ProcessingJob.created_at.desc())).all()
        for job in jobs:
            job.status=ProcessingStatus.FAILED
            job.error=str(exc)
        db.commit()
        raise HTTPException(422, f"Document processing failed: {exc}")


@router.get("/bids/{bid_id}")
def list_bid_documents(bid_id: str, user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.AUDITOR, Role.BIDDER)), db: Session = Depends(get_db)):
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
    rows = db.scalars(select(Document).where(Document.bid_id == bid.id).order_by(Document.created_at.desc())).all()
    return [{"id": str(d.id), "filename": d.original_filename, "status": d.status, "sha256": d.sha256, "size": d.file_size} for d in rows]

@router.get("/{document_id}")
def get_document(document_id:str,user=Depends(require_roles(Role.ADMIN,Role.OFFICER,Role.AUDITOR,Role.BIDDER)),db:Session=Depends(get_db)):
    d=db.get(Document,uuid.UUID(document_id))
    if not d: raise HTTPException(404,"Document not found")
    bid=db.get(Bid,d.bid_id)
    if user.role==Role.BIDDER:
        from app.models.entities import Bidder
        bidder=db.get(Bidder,bid.bidder_id)
        if not bidder or bidder.organization_id!=user.organization_id: raise HTTPException(403,"Forbidden")
    return {"id":str(d.id),"filename":d.original_filename,"sha256":d.sha256,"status":d.status,"storage_key":d.storage_key}
