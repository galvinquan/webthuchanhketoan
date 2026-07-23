from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.schemas.assignment import AssignmentOut


class ClassCreate(BaseModel):
    name: str


class ClassOut(BaseModel):
    id: int
    name: str
    teacher_id: int
    join_code: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JoinClassRequest(BaseModel):
    join_code: str


class AddCoTeacherRequest(BaseModel):
    username: str


class CoTeacherOut(BaseModel):
    teacher_id: int
    username: str
    role: str
    added_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentSubmissionOut(BaseModel):
    """Trạng thái nộp bài của 1 SV cho 1 assignment cụ thể."""
    assignment_id: int
    company_id: Optional[int] = None
    status: Optional[str] = None
    score: Optional[float] = None


class StudentInClassOut(BaseModel):
    user_id: int
    username: str
    joined_at: Optional[datetime] = None
    status: str
    submissions: list[StudentSubmissionOut] = []

    class Config:
        from_attributes = True


class ClassDetailOut(ClassOut):
    students: list[StudentInClassOut] = []
    assignments: list[AssignmentOut] = []
    co_teachers: list[CoTeacherOut] = []
