from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import AdmissionStatus, ApprovedIntake, StudentRecord


def compute_intake_summary(db: Session, institution_id: int, course_id: int, academic_year: str):
    intake = (
        db.query(ApprovedIntake)
        .filter_by(institution_id=institution_id, course_id=course_id, academic_year=academic_year)
        .first()
    )
    approved = intake.approved_intake if intake else 0
    admissions = (
        db.query(func.count(func.distinct(StudentRecord.apaar_ref)))
        .filter_by(
            institution_id=institution_id,
            course_id=course_id,
            academic_year=academic_year,
            admission_status=AdmissionStatus.active,
        )
        .scalar()
        or 0
    )
    remaining = max(approved - admissions, 0)
    excess = max(admissions - approved, 0)
    return {
        "approved_intake": approved,
        "recorded_admissions": admissions,
        "remaining_seats": remaining,
        "excess_admissions": excess,
        "status": "warning" if excess > 0 else "compliant",
    }
