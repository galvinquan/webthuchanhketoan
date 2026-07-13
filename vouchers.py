from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.models import Voucher, LedgerEntry, Company
from app.schemas.voucher import (
    VoucherCreate,
    VoucherUpdate,
    VoucherOut,
    VoucherDetailOut,
)
from app.services.accounting import post_voucher, AccountingError

router = APIRouter(prefix="/api/vouchers", tags=["vouchers"])


# ---------- auth/context dependency (giống pattern trong partners.py) ----------

def get_company_id(request: Request, db: Session = Depends(get_db)) -> int:
    user_id = request.cookies.get("user_id")
    if not user_id:
        raise HTTPException(401, "Chưa đăng nhập")
    company = db.query(Company).filter(Company.user_id == int(user_id)).first()
    if not company:
        raise HTTPException(404, "Chưa có thông tin doanh nghiệp")
    return company.id


# ---------- helpers ----------

def _get_voucher_or_404(db: Session, company_id: int, voucher_id: int) -> Voucher:
    voucher = (
        db.query(Voucher)
        .options(selectinload(Voucher.ledger_entries))
        .filter(Voucher.id == voucher_id, Voucher.company_id == company_id)
        .first()
    )
    if voucher is None:
        raise HTTPException(404, "Không tìm thấy phiếu")
    return voucher


def _is_posted(voucher: Voucher) -> bool:
    """Phiếu coi là đã duyệt nếu đã có bút toán sinh ra."""
    return len(voucher.ledger_entries) > 0


def _create_voucher(db: Session, company_id: int, voucher_type: str, payload: VoucherCreate) -> Voucher:
    voucher = Voucher(
        company_id=company_id,
        voucher_no=payload.voucher_no,
        voucher_type=voucher_type,
        cash_source=payload.cash_source,
        txn_kind=payload.txn_kind,
        partner_id=payload.partner_id,
        reason=payload.reason,
        voucher_date=payload.voucher_date,
        posting_date=payload.posting_date,
        attached_docs=payload.attached_docs or 0,
        total_amount=payload.total_amount,
    )
    db.add(voucher)
    db.commit()
    db.refresh(voucher)
    return voucher


def _update_voucher(
    db: Session, voucher: Voucher, expected_type: str, payload: VoucherUpdate
) -> Voucher:
    if voucher.voucher_type != expected_type:
        raise HTTPException(400, f"Phiếu này không phải phiếu {expected_type}")
    if _is_posted(voucher):
        raise HTTPException(400, "Phiếu đã duyệt, không thể sửa")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(voucher, field, value)

    db.commit()
    db.refresh(voucher)
    return voucher


def _delete_voucher(db: Session, voucher: Voucher, expected_type: str) -> None:
    if voucher.voucher_type != expected_type:
        raise HTTPException(400, f"Phiếu này không phải phiếu {expected_type}")
    if _is_posted(voucher):
        raise HTTPException(400, "Phiếu đã duyệt, không thể xóa")

    db.delete(voucher)
    db.commit()


# ---------- Phiếu thu (THU) ----------

@router.post("/receipts", response_model=VoucherOut)
def create_receipt(
    payload: VoucherCreate,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    if payload.voucher_type != "THU":
        raise HTTPException(400, "voucher_type phải là THU cho phiếu thu")
    return _create_voucher(db, company_id, "THU", payload)


@router.put("/receipts/{voucher_id}", response_model=VoucherOut)
def update_receipt(
    voucher_id: int,
    payload: VoucherUpdate,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    voucher = _get_voucher_or_404(db, company_id, voucher_id)
    return _update_voucher(db, voucher, "THU", payload)


@router.delete("/receipts/{voucher_id}")
def delete_receipt(
    voucher_id: int,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    voucher = _get_voucher_or_404(db, company_id, voucher_id)
    _delete_voucher(db, voucher, "THU")
    return {"message": "Đã xóa"}


# ---------- Phiếu chi (CHI) ----------

@router.post("/payments", response_model=VoucherOut)
def create_payment(
    payload: VoucherCreate,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    if payload.voucher_type != "CHI":
        raise HTTPException(400, "voucher_type phải là CHI cho phiếu chi")
    return _create_voucher(db, company_id, "CHI", payload)


@router.put("/payments/{voucher_id}", response_model=VoucherOut)
def update_payment(
    voucher_id: int,
    payload: VoucherUpdate,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    voucher = _get_voucher_or_404(db, company_id, voucher_id)
    return _update_voucher(db, voucher, "CHI", payload)


@router.delete("/payments/{voucher_id}")
def delete_payment(
    voucher_id: int,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    voucher = _get_voucher_or_404(db, company_id, voucher_id)
    _delete_voucher(db, voucher, "CHI")
    return {"message": "Đã xóa"}


# ---------- Chung: xem chi tiết, danh sách, duyệt ----------

@router.get("", response_model=list[VoucherOut])
def list_vouchers(
    voucher_type: str = None,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    q = db.query(Voucher).filter(Voucher.company_id == company_id)
    if voucher_type:
        q = q.filter(Voucher.voucher_type == voucher_type)
    return q.all()


@router.get("/{voucher_id}", response_model=VoucherDetailOut)
def get_voucher(
    voucher_id: int,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    return _get_voucher_or_404(db, company_id, voucher_id)


@router.post("/{voucher_id}/approve", response_model=VoucherDetailOut)
def approve_voucher(
    voucher_id: int,
    company_id: int = Depends(get_company_id),
    db: Session = Depends(get_db),
):
    """
    Duyệt phiếu thu/chi: sinh bút toán Nợ/Có tự động.
    - Validate tổng Nợ = tổng Có và khớp total_amount trước khi lưu (app/services/accounting.py).
    - Idempotent: nếu phiếu đã có bút toán rồi thì báo lỗi thay vì sinh trùng.
    """
    voucher = _get_voucher_or_404(db, company_id, voucher_id)

    if _is_posted(voucher):
        raise HTTPException(400, "Phiếu đã được duyệt trước đó")

    try:
        entries = post_voucher(voucher)
    except AccountingError as e:
        raise HTTPException(400, str(e))

    for entry in entries:
        db.add(entry)
    db.commit()
    db.refresh(voucher)
    return voucher
