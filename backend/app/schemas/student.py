from datetime import date, datetime

from pydantic import BaseModel, Field


class StudentBase(BaseModel):
    internal_record_id: str = Field(min_length=2, max_length=60)
    apaar_ref: str = Field(min_length=6, max_length=120)
    student_name: str = Field(min_length=2, max_length=255)
    date_of_birth: date
    institution_id: int
    course_id: int
    academic_year: str
    admission_date: date


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    student_name: str | None = None
    apaar_ref: str | None = None
    admission_status: str | None = None


class StudentOut(StudentBase):
    id: int
    admission_status: str
    verification_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
