from pydantic import BaseModel
from typing import Optional

class PartnerCreate(BaseModel):
    type: str  # CUSTOMER hoặc SUPPLIER
    code: Optional[str] = None
    name: str
    address: Optional[str] = None
    tax_code: Optional[str] = None
    goods_name: Optional[str] = None

class PartnerOut(BaseModel):
    id: int
    type: str
    code: Optional[str] = None
    name: str
    address: Optional[str] = None
    tax_code: Optional[str] = None
    goods_name: Optional[str] = None

    class Config:
        from_attributes = True