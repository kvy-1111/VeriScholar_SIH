from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import AuditEvent, CaseHistory, CaseStatus, InvestigationCase, StudentRecord
from app.schemas.case import CaseOut, CaseUpdate

router = APIRouter(prefix="/cases", tags=["cases"])

ALLOWED_TRANSITIONS = {
    CaseStatus.pending.value: {CaseStatus.under_review.value, CaseStatus.dismissed.value},
    CaseStatus.under_review.value: {CaseStatus.resolved.value, CaseStatus.dismissed.value},
    CaseStatus.resolved.value: set(),
    CaseStatus.dismissed.value: set(),
}


@router.post("")
def create_case(payload: dict, db: Session = Depends(get_db), user=Depends(require_roles("regulatory_admin"))):
    student = db.query(StudentRecord).filter(StudentRecord.id == payload["student_record_id"]).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student record not found")
    case = InvestigationCase(
        case_ref=payload["case_ref"],
        institution_id=student.institution_id,
        student_record_id=student.id,
        detection_reason=payload["detection_reason"],
        risk_score=payload["risk_score"],
    )
    db.add(case)
    db.add(CaseHistory(case_id=case.id, action="create", note="Case created", actor_id=user.id))
    db.add(AuditEvent(actor_id=user.id, action="case.create", resource_type="case", resource_id=payload["case_ref"], details="created"))
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=list[CaseOut])
def list_cases(db: Session = Depends(get_db), user=Depends(require_roles("college_admin", "regulatory_admin"))):
    return db.query(InvestigationCase).order_by(InvestigationCase.detected_at.desc()).all()


@router.patch("/{case_id}", response_model=CaseOut)
def update_case(case_id: int, payload: CaseUpdate, db: Session = Depends(get_db), user=Depends(require_roles("regulatory_admin"))):
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    current = case.status.value if hasattr(case.status, "value") else case.status
    if payload.status not in ALLOWED_TRANSITIONS[current]:
        raise HTTPException(status_code=400, detail="Invalid case status transition")

    case.status = payload.status
    case.reviewer_notes = payload.reviewer_notes
    db.add(CaseHistory(case_id=case.id, action="status_update", note=f"{current}->{payload.status}", actor_id=user.id))
    db.add(AuditEvent(actor_id=user.id, action="case.update", resource_type="case", resource_id=case.case_ref, details=f"status={payload.status}"))
    db.commit()
    db.refresh(case)
    return case
