from datetime import datetime

from pydantic import BaseModel


class CaseOut(BaseModel):
    id: int
    case_ref: str
    institution_id: int
    student_record_id: int
    detection_reason: str
    risk_score: int
    reviewer_notes: str | None
    status: str
    detected_at: datetime

    class Config:
        from_attributes = True


class CaseUpdate(BaseModel):
    status: str
    reviewer_notes: str | None = None
