from datetime import datetime

from dateutil.parser import parse
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.models import AuditEvent, StudentRecord, VerificationResult
from app.schemas.student import StudentCreate, StudentOut, StudentUpdate
from app.services.csv_utils import parse_csv_with_validation
from app.services.verification import detect_duplicates, verify_student_record

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentOut)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("college_admin", "regulatory_admin")),
):
    record = StudentRecord(**payload.model_dump())
    db.add(record)
    db.flush()

    status, message = verify_student_record(db, record)
    record.verification_status = status
    db.add(VerificationResult(student_record_id=record.id, status=status, message=message, source="simulated"))
    db.add(AuditEvent(actor_id=user.id, action="student.create", resource_type="student_record", resource_id=str(record.id), details="created"))
    db.commit()
    db.refresh(record)
    return record


@router.get("", response_model=list[StudentOut])
def list_students(
    db: Session = Depends(get_db),
    user=Depends(require_roles("college_admin", "regulatory_admin", "student")),
    institution_id: int | None = None,
    course_id: int | None = None,
    academic_year: str | None = None,
    skip: int = 0,
    limit: int = Query(default=20, le=200),
):
    q = db.query(StudentRecord)
    if user.role.value == "student":
        q = q.filter(StudentRecord.id == user.student_record_id)
    if institution_id:
        q = q.filter(StudentRecord.institution_id == institution_id)
    if course_id:
        q = q.filter(StudentRecord.course_id == course_id)
    if academic_year:
        q = q.filter(StudentRecord.academic_year == academic_year)
    return q.order_by(StudentRecord.created_at.desc()).offset(skip).limit(limit).all()


@router.patch("/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int,
    payload: StudentUpdate,
    db: Session = Depends(get_db),
    user=Depends(require_roles("college_admin", "regulatory_admin")),
):
    record = db.query(StudentRecord).filter(StudentRecord.id == student_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Student record not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(record, k, v)
    record.updated_at = datetime.utcnow()
    db.add(AuditEvent(actor_id=user.id, action="student.update", resource_type="student_record", resource_id=str(student_id), details="updated"))
    db.commit()
    db.refresh(record)
    return record


@router.delete("/{student_id}")
def deactivate_student(
    student_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_roles("college_admin", "regulatory_admin")),
):
    record = db.query(StudentRecord).filter(StudentRecord.id == student_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Student record not found")
    record.admission_status = "deactivated"
    db.add(AuditEvent(actor_id=user.id, action="student.deactivate", resource_type="student_record", resource_id=str(student_id), details="deactivated"))
    db.commit()
    return {"detail": "Student record deactivated"}


@router.post("/upload-csv")
async def upload_students_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_roles("college_admin", "regulatory_admin")),
):
    if file.content_type not in {"text/csv", "application/vnd.ms-excel"}:
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    content = await file.read()
    valid_rows, errors = parse_csv_with_validation(content)
    duplicate_refs = detect_duplicates(valid_rows)
    for row in valid_rows:
        if row["apaar_ref"] in duplicate_refs:
            errors.append({"row": row.get("internal_record_id"), "field": "apaar_ref", "error": "Potential duplicate in upload"})

    created = 0
    for row in valid_rows:
        if row["apaar_ref"] in duplicate_refs:
            continue
        db.add(
            StudentRecord(
                internal_record_id=row["internal_record_id"],
                apaar_ref=row["apaar_ref"],
                student_name=row["student_name"],
                date_of_birth=parse(str(row["date_of_birth"])).date(),
                institution_id=int(row["institution_id"]),
                course_id=int(row["course_id"]),
                academic_year=str(row["academic_year"]),
                admission_date=parse(str(row["admission_date"])).date(),
            )
        )
        created += 1

    db.add(AuditEvent(actor_id=user.id, action="student.csv_upload", resource_type="student_record", resource_id="bulk", details=f"created={created}; errors={len(errors)}"))
    db.commit()
    return {"created": created, "errors": errors}
