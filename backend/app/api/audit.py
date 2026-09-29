import uuid
from fastapi import APIRouter,Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.entities import AuditLog,Role
router=APIRouter(prefix="/audit",tags=["audit"])
@router.get("")
def audit(user=Depends(require_roles(Role.ADMIN, Role.OFFICER, Role.MINISTRY_OFFICER, Role.AUDITOR)), db: Session = Depends(get_db)):
    rows=db.scalars(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200)).all()
    return [{"id":str(x.id),"actor_id":str(x.actor_id) if x.actor_id else None,"action":x.action,"entity_type":x.entity_type,
             "entity_id":x.entity_id,"timestamp":x.timestamp,"previous_hash":x.previous_hash,"current_hash":x.current_hash} for x in rows]
