from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional


class CompanyCreate(BaseModel):
    assignment_id: int
    name: str
    address: Optional[str] = None
    tax_code: Optional[str] = None
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    period_from: date
    period_to: date


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    tax_code: Optional[str] = None
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    period_from: Optional[date] = None
    period_to: Optional[date] = None


class SubmitRequest(BaseModel):
    """Sinh viên xác nhận nộp bài (chuyển status -> submitted)."""
    pass


class GradeRequest(BaseModel):
    score: float
    feedback: Optional[str] = None

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v):
        if not (0 <= v <= 10):
            raise ValueError("score phải trong khoảng 0-10")
        return v


class CompanyOut(BaseModel):
    id: int
    assignment_id: Optional[int] = None
    name: str
    address: Optional[str] = None
    tax_code: Optional[str] = None
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    period_from: date
    period_to: date
    status: str
    score: Optional[float] = None
    feedback: Optional[str] = None
    graded_by: Optional[int] = None
    graded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
