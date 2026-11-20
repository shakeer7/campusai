import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.workflow import AuditLog

logger = logging.getLogger(__name__)


def log_audit(
    db: Session,
    user_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None
) -> AuditLog:
    """Creates an immutable audit log entry in the database."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=details or {},
        ip_address=ip_address
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.info(f"Audit log recorded: user={user_id} action={action} entity={entity_type}:{entity_id}")
    return entry
