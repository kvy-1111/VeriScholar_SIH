from app.models.models import AdmissionStatus, ApprovedIntake, Course, Institution, StudentRecord
from app.services.compliance import compute_intake_summary


def test_compliance_uses_distinct_identifiers(db_session):
    inst = Institution(name="Inst", code="I1", status="active")
    course = Course(name="Course")
    db_session.add_all([inst, course])
    db_session.flush()

    db_session.add(ApprovedIntake(institution_id=inst.id, course_id=course.id, academic_year="2026-27", approved_intake=1))
    db_session.add_all(
        [
            StudentRecord(internal_record_id="1", apaar_ref="APAAR-DEMO-001", student_name="A", date_of_birth="2000-01-01", institution_id=inst.id, course_id=course.id, academic_year="2026-27", admission_date="2026-06-01", admission_status=AdmissionStatus.active),
            StudentRecord(internal_record_id="2", apaar_ref="APAAR-DEMO-001", student_name="A", date_of_birth="2000-01-01", institution_id=inst.id, course_id=course.id, academic_year="2026-27", admission_date="2026-06-01", admission_status=AdmissionStatus.active),
            StudentRecord(internal_record_id="3", apaar_ref="APAAR-DEMO-002", student_name="B", date_of_birth="2000-01-01", institution_id=inst.id, course_id=course.id, academic_year="2026-27", admission_date="2026-06-01", admission_status=AdmissionStatus.active),
        ]
    )
    db_session.commit()

    summary = compute_intake_summary(db_session, inst.id, course.id, "2026-27")
    assert summary["recorded_admissions"] == 2
    assert summary["excess_admissions"] == 1
