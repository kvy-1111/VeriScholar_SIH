"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_table("courses", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(length=255), nullable=False))
    op.create_table(
        "student_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("internal_record_id", sa.String(length=60), nullable=False),
        sa.Column("apaar_ref", sa.String(length=120), nullable=False),
        sa.Column("student_name", sa.String(length=255), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("admission_date", sa.Date(), nullable=False),
        sa.Column("admission_status", sa.String(length=20), nullable=False),
        sa.Column("verification_status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("institution_id", "internal_record_id", name="uq_institution_internal_id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id")),
        sa.Column("student_record_id", sa.Integer(), sa.ForeignKey("student_records.id")),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "approved_intakes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("academic_year", sa.String(length=20), nullable=False),
        sa.Column("approved_intake", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("institution_id", "course_id", "academic_year", name="uq_intake"),
    )
    op.create_table(
        "verification_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_record_id", sa.Integer(), sa.ForeignKey("student_records.id"), nullable=False),
        sa.Column("status", sa.String(length=60), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("student_record_id"),
    )
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_record_id", sa.Integer(), sa.ForeignKey("student_records.id"), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False),
        sa.Column("reasons", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("student_record_id"),
    )
    op.create_table(
        "investigation_cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_ref", sa.String(length=40), nullable=False),
        sa.Column("institution_id", sa.Integer(), sa.ForeignKey("institutions.id"), nullable=False),
        sa.Column("student_record_id", sa.Integer(), sa.ForeignKey("student_records.id"), nullable=False),
        sa.Column("detection_reason", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Integer(), nullable=False),
        sa.Column("assigned_reviewer_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("reviewer_notes", sa.Text()),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("case_ref"),
    )
    op.create_table(
        "case_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("investigation_cases.id"), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("resource_type", sa.String(length=80), nullable=False),
        sa.Column("resource_id", sa.String(length=80), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "qr_credentials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("credential_ref", sa.String(length=64), nullable=False),
        sa.Column("student_record_id", sa.Integer(), sa.ForeignKey("student_records.id"), nullable=False),
        sa.Column("signed_payload", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("credential_ref"),
    )


def downgrade() -> None:
    op.drop_table("qr_credentials")
    op.drop_table("audit_events")
    op.drop_table("case_history")
    op.drop_table("investigation_cases")
    op.drop_table("risk_assessments")
    op.drop_table("verification_results")
    op.drop_table("approved_intakes")
    op.drop_table("users")
    op.drop_table("student_records")
    op.drop_table("courses")
    op.drop_table("institutions")
