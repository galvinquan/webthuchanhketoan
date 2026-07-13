from pydantic import BaseModel, field_validator
from datetime import date
from decimal import Decimal
from typing import Optional, Literal


# voucher_type: "THU" (phiếu thu) | "CHI" (phiếu chi)
# cash_source : "TM"  (tiền mặt)   | "TGNH" (tiền gửi ngân hàng)
VoucherType = Literal["THU", "CHI"]
CashSource = Literal["TM", "TGNH"]


class VoucherCreate(BaseModel):
    voucher_no: str
    voucher_type: VoucherType
    cash_source: CashSource
    txn_kind: str          # loại nghiệp vụ, dùng để map sang TK đối ứng, vd "THU_NO_KH", "CHI_MUA_HANG"
    partner_id: Optional[int] = None
    reason: Optional[str] = None
    voucher_date: date
    posting_date: date
    attached_docs: Optional[int] = 0
    total_amount: Decimal

    @field_validator("total_amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("total_amount phải lớn hơn 0")
        return v


class VoucherUpdate(BaseModel):
    voucher_no: Optional[str] = None
    cash_source: Optional[CashSource] = None
    txn_kind: Optional[str] = None
    partner_id: Optional[int] = None
    reason: Optional[str] = None
    voucher_date: Optional[date] = None
    posting_date: Optional[date] = None
    attached_docs: Optional[int] = None
    total_amount: Optional[Decimal] = None

    @field_validator("total_amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("total_amount phải lớn hơn 0")
        return v


class LedgerEntryOut(BaseModel):
    id: int
    voucher_id: int
    company_id: int
    posting_date: date
    narration: Optional[str] = None
    debit_acct: str
    credit_acct: str
    amount: Decimal
    partner_id: Optional[int] = None

    class Config:
        from_attributes = True


class VoucherOut(BaseModel):
    id: int
    company_id: int
    voucher_no: str
    voucher_type: str
    cash_source: str
    txn_kind: str
    partner_id: Optional[int] = None
    reason: Optional[str] = None
    voucher_date: date
    posting_date: date
    attached_docs: int
    total_amount: Decimal

    class Config:
        from_attributes = True


class VoucherDetailOut(VoucherOut):
    ledger_entries: list[LedgerEntryOut] = []
