from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class AssignmentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None


class AssignmentOut(BaseModel):
    id: int
    class_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    created_by: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
