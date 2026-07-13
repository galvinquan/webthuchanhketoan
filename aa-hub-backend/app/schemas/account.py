from pydantic import BaseModel
from typing import Optional

class AccountOut(BaseModel):
    number: str
    name: str
    level: int
    parent_number: Optional[str] = None
    acct_class: int
    balance_nature: str

    class Config:
        from_attributes = True

class OpeningBalanceUpdate(BaseModel):
    account_number: str
    partner_id: Optional[int] = None
    debit: float = 0
    credit: float = 0

class OpeningBalanceOut(BaseModel):
    account_number: str
    partner_id: Optional[int] = None
    debit: float
    credit: float

    class Config:
        from_attributes = True