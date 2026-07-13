from pydantic import BaseModel
from datetime import date
from typing import Optional

class CompanyCreate(BaseModel):
    name: str
    address: Optional[str] = None
    tax_code: Optional[str] = None
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    period_from: date
    period_to: date

class CompanyOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    tax_code: Optional[str] = None
    student_name: Optional[str] = None
    class_name: Optional[str] = None
    period_from: date
    period_to: date

    class Config:
        from_attributes = True