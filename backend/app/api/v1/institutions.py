from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import ApprovedIntake, AuditEvent, Course, Institution
from app.services.compliance import compute_intake_summary

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.post("")
def create_institution(payload: dict, db: Session = Depends(get_db), user=Depends(require_roles("regulatory_admin"))):
    inst = Institution(name=payload["name"], code=payload["code"], status=payload.get("status", "active"))
    db.add(inst)
    db.add(AuditEvent(actor_id=user.id, action="institution.create", resource_type="institution", resource_id=payload["code"], details="created"))
    db.commit()
    db.refresh(inst)
    return inst


@router.get("")
def list_institutions(db: Session = Depends(get_db), user=Depends(require_roles("college_admin", "regulatory_admin"))):
    return db.query(Institution).all()


@router.post("/courses")
def create_course(payload: dict, db: Session = Depends(get_db), user=Depends(require_roles("regulatory_admin"))):
    course = Course(name=payload["name"])
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.post("/approved-intakes")
def upsert_intake(payload: dict, db: Session = Depends(get_db), user=Depends(require_roles("regulatory_admin"))):
    intake = (
        db.query(ApprovedIntake)
        .filter_by(institution_id=payload["institution_id"], course_id=payload["course_id"], academic_year=payload["academic_year"])
        .first()
    )
    if intake:
        intake.approved_intake = payload["approved_intake"]
    else:
        intake = ApprovedIntake(**payload)
        db.add(intake)
    db.add(AuditEvent(actor_id=user.id, action="intake.upsert", resource_type="approved_intake", resource_id=f"{payload['institution_id']}-{payload['course_id']}-{payload['academic_year']}", details=f"approved_intake={payload['approved_intake']}"))
    db.commit()
    return {"detail": "Approved intake updated"}


@router.get("/compliance")
def compliance(institution_id: int, course_id: int, academic_year: str, db: Session = Depends(get_db), user=Depends(require_roles("college_admin", "regulatory_admin"))):
    return compute_intake_summary(db, institution_id, course_id, academic_year)
