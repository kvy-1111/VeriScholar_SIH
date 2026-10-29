from datetime import date

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.models import (
    AdmissionStatus,
    ApprovedIntake,
    CaseStatus,
    Course,
    Institution,
    InvestigationCase,
    Role,
    StudentRecord,
    User,
    VerificationStatus,
)
from app.services.risk import calculate_risk_score


def get_or_create(db, model, defaults=None, **kwargs):
    instance = db.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    params = {**kwargs, **(defaults or {})}
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance


def run_seed():
    db = SessionLocal()
    try:
        alpha = get_or_create(db, Institution, name="Alpha Institute of Technology", code="AIT001", status="active")
        beta = get_or_create(db, Institution, name="Beta College of Engineering", code="BCE002", status="active")
        gamma = get_or_create(db, Institution, name="Gamma School of Management", code="GSM003", status="active")

        cs = get_or_create(db, Course, name="B.Tech Computer Science")
        mech = get_or_create(db, Course, name="B.Tech Mechanical")

        get_or_create(db, ApprovedIntake, institution_id=alpha.id, course_id=cs.id, academic_year="2026-27", approved_intake=3)
        get_or_create(db, ApprovedIntake, institution_id=beta.id, course_id=cs.id, academic_year="2026-27", approved_intake=2)
        get_or_create(db, ApprovedIntake, institution_id=gamma.id, course_id=mech.id, academic_year="2026-27", approved_intake=2)

        records = [
            {"internal_record_id": "AIT-CS-001", "apaar_ref": "APAAR-DEMO-000001", "student_name": "Aarav Menon", "date_of_birth": date(2006, 1, 12), "institution_id": alpha.id, "course_id": cs.id, "academic_year": "2026-27", "admission_date": date(2026, 6, 10), "verification_status": VerificationStatus.valid_format},
            {"internal_record_id": "AIT-CS-002", "apaar_ref": "APAAR-DEMO-000002", "student_name": "Isha Reddy", "date_of_birth": date(2006, 3, 20), "institution_id": alpha.id, "course_id": cs.id, "academic_year": "2026-27", "admission_date": date(2026, 6, 12), "verification_status": VerificationStatus.valid_format},
            {"internal_record_id": "AIT-CS-003", "apaar_ref": "APAAR-DEMO-000003", "student_name": "Kabir Shah", "date_of_birth": date(2006, 2, 3), "institution_id": alpha.id, "course_id": cs.id, "academic_year": "2026-27", "admission_date": date(2026, 6, 15), "verification_status": VerificationStatus.valid_format},
            {"internal_record_id": "AIT-CS-004", "apaar_ref": "APAAR-DEMO-000004", "student_name": "Maya Singh", "date_of_birth": date(2006, 7, 19), "institution_id": alpha.id, "course_id": cs.id, "academic_year": "2026-27", "admission_date": date(2026, 6, 18), "verification_status": VerificationStatus.potential_duplicate},
            {"internal_record_id": "BCE-CS-001", "apaar_ref": "APAAR-DEMO-000004", "student_name": "Maya S.", "date_of_birth": date(2006, 7, 19), "institution_id": beta.id, "course_id": cs.id, "academic_year": "2026-27", "admission_date": date(2026, 6, 11), "verification_status": VerificationStatus.identity_mismatch},
            {"internal_record_id": "BCE-CS-002", "apaar_ref": "APAAR-DEMO-000005", "student_name": "Nikhil Verma", "date_of_birth": date(2006, 9, 1), "institution_id": beta.id, "course_id": cs.id, "academic_year": "2026-27", "admission_date": date(2026, 6, 9), "verification_status": VerificationStatus.pending},
        ]

        for data in records:
            get_or_create(db, StudentRecord, **data)

        college_admin = get_or_create(db, User, email="college.admin@verischolar.demo", defaults={"password_hash": get_password_hash("Demo@123"), "role": Role.college_admin, "institution_id": alpha.id, "is_active": True})
        reg_admin = get_or_create(db, User, email="reg.admin@verischolar.demo", defaults={"password_hash": get_password_hash("Demo@123"), "role": Role.regulatory_admin, "is_active": True})
        student_record = db.query(StudentRecord).filter_by(internal_record_id="AIT-CS-001").first()
        get_or_create(db, User, email="student@verischolar.demo", defaults={"password_hash": get_password_hash("Demo@123"), "role": Role.student, "student_record_id": student_record.id if student_record else None, "is_active": True})

        target = db.query(StudentRecord).filter_by(internal_record_id="BCE-CS-001").first()
        if target:
            risk = calculate_risk_score(target.verification_status.value, is_above_intake=True, has_missing_fields=False, repeated_quality_issues=2, cross_institution_unusual=True)
            get_or_create(db, InvestigationCase, case_ref="CASE-2026-0001", defaults={"institution_id": target.institution_id, "student_record_id": target.id, "detection_reason": ", ".join(risk["reasons"]), "risk_score": risk["score"], "status": CaseStatus.pending})

        db.commit()
        print("Synthetic seed completed. Safe to rerun.")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
