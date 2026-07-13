from pydantic import BaseModel
from typing import Optional

class JournalLine(BaseModel):
    posting_date: str
    voucher_no: str
    voucher_type: str
    narration: Optional[str] = None
    debit_acct: str
    credit_acct: str
    amount: float

class TrialBalanceRow(BaseModel):
    account_number: str
    account_name: str
    opening_debit: float
    opening_credit: float
    period_debit: float
    period_credit: float
    closing_debit: float
    closing_credit: float