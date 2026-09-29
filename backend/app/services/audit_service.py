import hashlib
import json
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.entities import AuditLog


def log_event(db, actor_id, action, entity_type, entity_id, metadata=None, ip=None):
    previous = db.scalars(select(AuditLog).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())).first()
    prev = previous.current_hash if previous else ""
    ts = datetime.now(timezone.utc)
    body = json.dumps({
        "actor_id": str(actor_id) if actor_id else None,
        "action": action,
        "entity_type": entity_type,
        "entity_id": str(entity_id),
        "metadata": metadata or {},
        "previous_hash": prev,
    }, sort_keys=True, default=str)
    current = hashlib.sha256((prev + body).encode()).hexdigest()
    row = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        timestamp=ts,
        metadata_json=metadata or {},
        ip_address=ip,
        previous_hash=prev,
        current_hash=current,
    )
    db.add(row)
    db.commit()
    return row
