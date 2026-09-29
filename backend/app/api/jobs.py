import uuid
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import current_user
from app.models.entities import ProcessingJob
router=APIRouter(prefix="/jobs",tags=["jobs"])
@router.get("/{job_id}")
def get_job(job_id:str,user=Depends(current_user),db:Session=Depends(get_db)):
    try:
        jid=uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(400,"Invalid job_id")
    j=db.get(ProcessingJob,jid)
    if not j: raise HTTPException(404,"Job not found")
    return {"id":str(j.id),"type":j.job_type,"status":j.status,"progress":j.progress,"error":j.error}
