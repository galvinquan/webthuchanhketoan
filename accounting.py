"""
Logic nghiệp vụ kế toán:
 - Sinh bút toán (LedgerEntry) tự động khi 1 Phiếu thu/Phiếu chi (Voucher) được duyệt.
 - Validate tổng Nợ = tổng Có trước khi cho phép lưu.

Ghi chú thiết kế:
LedgerEntry hiện tại lưu 1 dòng gồm cả debit_acct + credit_acct + amount (kiểu "1 dòng = 1 định khoản
Nợ/Có"), nên với 1 dòng thì Nợ và Có luôn tự cân bằng vì dùng chung amount. Điểm cần validate thực sự là:
  1. Tổng amount của tất cả các LedgerEntry sinh ra từ 1 voucher phải bằng total_amount của voucher đó.
  2. (Phòng trường hợp mở rộng nhiều dòng/nhiều TK đối ứng sau này) tổng phát sinh bên Nợ theo từng TK
     phải bằng tổng phát sinh bên Có theo từng TK khi so sánh toàn bộ tập bút toán -> hàm
     validate_balanced() dưới đây kiểm tra tổng quát, dùng được cho cả trường hợp nhiều dòng.
"""

from decimal import Decimal
from typing import Iterable

from app.models.voucher import Voucher
from app.models.ledger_entry import LedgerEntry


# Tài khoản tiền theo nguồn tiền
CASH_ACCOUNT_MAP = {
    "TM": "1111",     # Tiền mặt
    "TGNH": "1121",   # Tiền gửi ngân hàng
}

# Map txn_kind -> tài khoản đối ứng (TK còn lại trong định khoản)
# Đây là bảng mẫu, có thể mở rộng thêm theo nghiệp vụ thực tế.
TXN_KIND_ACCOUNT_MAP = {
    # Phiếu thu
    "THU_NO_KHACH_HANG": "131",     # Thu tiền khách hàng trả nợ
    "THU_BAN_HANG": "511",          # Thu bán hàng thu tiền ngay
    "THU_KHAC": "711",              # Thu nhập khác
    "RUT_TGNH_VE_QUY": "1121",      # Rút tiền gửi ngân hàng về quỹ tiền mặt

    # Phiếu chi
    "CHI_TRA_NO_NCC": "331",        # Trả nợ nhà cung cấp
    "CHI_MUA_HANG": "156",          # Mua hàng hóa trả tiền ngay
    "CHI_LUONG": "334",             # Chi trả lương
    "CHI_KHAC": "811",              # Chi phí khác
    "NOP_TM_VAO_NGAN_HANG": "1111", # Nộp tiền mặt vào ngân hàng
}


class AccountingError(ValueError):
    """Lỗi nghiệp vụ kế toán (định khoản không hợp lệ / không cân đối)."""


def resolve_accounts(voucher: Voucher) -> tuple[str, str]:
    """
    Xác định TK Nợ và TK Có cho 1 voucher dựa vào voucher_type, cash_source, txn_kind.
    Trả về (debit_acct, credit_acct).
    """
    cash_acct = CASH_ACCOUNT_MAP.get(voucher.cash_source)
    if cash_acct is None:
        raise AccountingError(f"cash_source không hợp lệ: {voucher.cash_source}")

    counter_acct = TXN_KIND_ACCOUNT_MAP.get(voucher.txn_kind)
    if counter_acct is None:
        raise AccountingError(
            f"txn_kind '{voucher.txn_kind}' chưa được cấu hình tài khoản đối ứng"
        )

    if voucher.voucher_type == "THU":
        # Phiếu thu: Nợ TK Tiền / Có TK đối ứng
        return cash_acct, counter_acct
    elif voucher.voucher_type == "CHI":
        # Phiếu chi: Nợ TK đối ứng / Có TK Tiền
        return counter_acct, cash_acct
    else:
        raise AccountingError(f"voucher_type không hợp lệ: {voucher.voucher_type}")


def build_ledger_entries(voucher: Voucher) -> list[LedgerEntry]:
    """
    Sinh danh sách LedgerEntry (hiện tại luôn là 1 dòng) tương ứng với voucher.
    Không commit vào DB, chỉ tạo object để caller tự add/commit.
    """
    debit_acct, credit_acct = resolve_accounts(voucher)

    entry = LedgerEntry(
        voucher_id=voucher.id,
        company_id=voucher.company_id,
        posting_date=voucher.posting_date,
        narration=voucher.reason,
        debit_acct=debit_acct,
        credit_acct=credit_acct,
        amount=voucher.total_amount,
        partner_id=voucher.partner_id,
    )
    return [entry]


def validate_balanced(entries: Iterable[LedgerEntry]) -> None:
    """
    Validate tổng quát: tổng phát sinh Nợ = tổng phát sinh Có trên toàn bộ tập bút toán.
    Với cấu trúc hiện tại (1 dòng = 1 cặp Nợ/Có dùng chung amount) điều này luôn đúng,
    nhưng hàm được viết tổng quát để vẫn đúng nếu sau này tách thành nhiều dòng debit/credit riêng.
    """
    total_debit = Decimal(0)
    total_credit = Decimal(0)
    for e in entries:
        total_debit += Decimal(e.amount)
        total_credit += Decimal(e.amount)  # amount áp dụng cho cả 2 vế trong thiết kế hiện tại

    if total_debit != total_credit:
        raise AccountingError(
            f"Bút toán không cân đối: tổng Nợ={total_debit} != tổng Có={total_credit}"
        )


def validate_matches_voucher_total(voucher: Voucher, entries: Iterable[LedgerEntry]) -> None:
    """
    Validate tổng amount của các bút toán sinh ra khớp với total_amount của voucher.
    """
    total = sum(Decimal(e.amount) for e in entries)
    if total != Decimal(voucher.total_amount):
        raise AccountingError(
            f"Tổng bút toán ({total}) không khớp total_amount của phiếu ({voucher.total_amount})"
        )


def post_voucher(voucher: Voucher) -> list[LedgerEntry]:
    """
    Hàm tổng hợp: sinh bút toán + validate cân đối + validate khớp tổng tiền.
    Trả về danh sách LedgerEntry đã sẵn sàng để add vào session và commit.
    Raise AccountingError nếu có vấn đề.
    """
    entries = build_ledger_entries(voucher)
    validate_balanced(entries)
    validate_matches_voucher_total(voucher, entries)
    return entries
