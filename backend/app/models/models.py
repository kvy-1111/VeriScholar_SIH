from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Role(str, Enum):
    student = "student"
    college_admin = "college_admin"
    regulatory_admin = "regulatory_admin"


class AdmissionStatus(str, Enum):
    active = "active"
    deactivated = "deactivated"


class VerificationStatus(str, Enum):
    pending = "pending"
    valid_format = "valid_format"
    potential_duplicate = "potential_duplicate"
    identity_mismatch = "identity_mismatch"
    verified_simulated = "verified_simulated"


class CaseStatus(str, Enum):
    pending = "pending"
    under_review = "under_review"
    resolved = "resolved"
    dismissed = "dismissed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(SQLEnum(Role), index=True)
    institution_id: Mapped[int | None] = mapped_column(ForeignKey("institutions.id"), nullable=True)
    student_record_id: Mapped[int | None] = mapped_column(ForeignKey("student_records.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)


class ApprovedIntake(Base):
    __tablename__ = "approved_intakes"
    __table_args__ = (UniqueConstraint("institution_id", "course_id", "academic_year", name="uq_intake"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    academic_year: Mapped[str] = mapped_column(String(20), index=True)
    approved_intake: Mapped[int] = mapped_column(Integer)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StudentRecord(Base):
    __tablename__ = "student_records"
    __table_args__ = (UniqueConstraint("institution_id", "internal_record_id", name="uq_institution_internal_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    internal_record_id: Mapped[str] = mapped_column(String(60), index=True)
    apaar_ref: Mapped[str] = mapped_column(String(120), index=True)
    student_name: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[datetime] = mapped_column(Date)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    academic_year: Mapped[str] = mapped_column(String(20), index=True)
    admission_date: Mapped[datetime] = mapped_column(Date)
    admission_status: Mapped[AdmissionStatus] = mapped_column(SQLEnum(AdmissionStatus), default=AdmissionStatus.active)
    verification_status: Mapped[VerificationStatus] = mapped_column(SQLEnum(VerificationStatus), default=VerificationStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_record_id: Mapped[int] = mapped_column(ForeignKey("student_records.id"), unique=True)
    status: Mapped[str] = mapped_column(String(60))
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(80), default="simulated")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_record_id: Mapped[int] = mapped_column(ForeignKey("student_records.id"), unique=True)
    score: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(20))
    reasons: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_ref: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    institution_id: Mapped[int] = mapped_column(ForeignKey("institutions.id"), index=True)
    student_record_id: Mapped[int] = mapped_column(ForeignKey("student_records.id"), index=True)
    detection_reason: Mapped[str] = mapped_column(Text)
    risk_score: Mapped[int] = mapped_column(Integer)
    assigned_reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(SQLEnum(CaseStatus), default=CaseStatus.pending)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CaseHistory(Base):
    __tablename__ = "case_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("investigation_cases.id"), index=True)
    action: Mapped[str] = mapped_column(String(60))
    note: Mapped[str] = mapped_column(Text)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(80))
    details: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class QRCredential(Base):
    __tablename__ = "qr_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    credential_ref: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    student_record_id: Mapped[int] = mapped_column(ForeignKey("student_records.id"), index=True)
    signed_payload: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
