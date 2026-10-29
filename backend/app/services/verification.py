from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.models.models import StudentRecord, VerificationStatus


def validate_identifier_format(apaar_ref: str) -> bool:
    return apaar_ref.startswith("APAAR-") and len(apaar_ref) >= 12


def detect_duplicates(records: list[dict[str, Any]]) -> set[str]:
    counts = Counter((r.get("apaar_ref") or "").strip() for r in records if r.get("apaar_ref"))
    return {ref for ref, count in counts.items() if count > 1}


def verify_student_record(db: Session, record: StudentRecord) -> tuple[str, str]:
    missing = []
    for field in ["internal_record_id", "apaar_ref", "student_name", "academic_year"]:
        if not getattr(record, field):
            missing.append(field)
    if missing:
        return VerificationStatus.pending.value, f"Missing information: {', '.join(missing)}"

    if not validate_identifier_format(record.apaar_ref):
        return VerificationStatus.pending.value, "Identifier format invalid"

    duplicate = (
        db.query(StudentRecord)
        .filter(StudentRecord.apaar_ref == record.apaar_ref, StudentRecord.id != record.id)
        .first()
    )
    if duplicate:
        if duplicate.student_name.lower() != record.student_name.lower() or duplicate.date_of_birth != record.date_of_birth:
            return VerificationStatus.identity_mismatch.value, "Possible identity mismatch across matching identifier"
        return VerificationStatus.potential_duplicate.value, "Potential duplicate admission across institutions"

    return VerificationStatus.valid_format.value, "Valid format check; official verification pending (simulated)"
