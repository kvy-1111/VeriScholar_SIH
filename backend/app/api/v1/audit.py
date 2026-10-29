from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), user=Depends(require_roles("regulatory_admin"))):
    return db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).offset(skip).limit(limit).all()
