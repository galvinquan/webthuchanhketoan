"""
Test cases cơ bản cho luồng: tạo phiếu thu/chi -> duyệt -> sinh đúng bút toán -> cân đối.

Chạy bằng: pytest tests/test_voucher.py -v
Yêu cầu: pytest, pytest sẽ dùng SQLite in-memory để không phụ thuộc Postgres thật.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.company import Company
from app.models.user import User
from app.models.account import Account
from app.models.voucher import Voucher
from app.services.accounting import post_voucher, AccountingError, TXN_KIND_ACCOUNT_MAP


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()

    # seed dữ liệu tối thiểu
    user = User(username="student1", password="hashed", role="student")
    session.add(user)
    session.commit()

    company = Company(
        user_id=user.id,
        name="Cong ty Test",
        period_from=date(2025, 1, 1),
        period_to=date(2025, 12, 31),
    )
    session.add(company)
    session.commit()

    # cần các tài khoản dùng trong TXN_KIND_ACCOUNT_MAP + tiền mặt/ngân hàng
    accounts = [
        Account(number="1111", name="Tien mat", level=1, acct_class=1, balance_nature="DEBIT"),
        Account(number="1121", name="Tien gui ngan hang", level=1, acct_class=1, balance_nature="DEBIT"),
        Account(number="131", name="Phai thu khach hang", level=1, acct_class=1, balance_nature="DEBIT"),
        Account(number="331", name="Phai tra nguoi ban", level=1, acct_class=1, balance_nature="CREDIT"),
    ]
    session.add_all(accounts)
    session.commit()

    yield session, company

    session.close()


def _make_receipt(company_id: int, **overrides) -> Voucher:
    defaults = dict(
        company_id=company_id,
        voucher_no="PT001",
        voucher_type="THU",
        cash_source="TM",
        txn_kind="THU_NO_KHACH_HANG",
        partner_id=None,
        reason="Thu no khach hang A",
        voucher_date=date(2025, 3, 1),
        posting_date=date(2025, 3, 1),
        attached_docs=1,
        total_amount=Decimal("1000000"),
    )
    defaults.update(overrides)
    return Voucher(**defaults)


def _make_payment(company_id: int, **overrides) -> Voucher:
    defaults = dict(
        company_id=company_id,
        voucher_no="PC001",
        voucher_type="CHI",
        cash_source="TGNH",
        txn_kind="CHI_TRA_NO_NCC",
        partner_id=None,
        reason="Tra no nha cung cap B",
        voucher_date=date(2025, 3, 2),
        posting_date=date(2025, 3, 2),
        attached_docs=1,
        total_amount=Decimal("500000"),
    )
    defaults.update(overrides)
    return Voucher(**defaults)


def test_create_receipt_and_approve_generates_correct_entry(db_session):
    session, company = db_session

    voucher = _make_receipt(company.id)
    session.add(voucher)
    session.commit()
    session.refresh(voucher)

    entries = post_voucher(voucher)
    for e in entries:
        session.add(e)
    session.commit()

    assert len(entries) == 1
    entry = entries[0]
    # Phiếu thu tiền mặt thu nợ khách hàng: Nợ 1111 / Có 131
    assert entry.debit_acct == "1111"
    assert entry.credit_acct == "131"
    assert entry.amount == Decimal("1000000")


def test_create_payment_and_approve_generates_correct_entry(db_session):
    session, company = db_session

    voucher = _make_payment(company.id)
    session.add(voucher)
    session.commit()
    session.refresh(voucher)

    entries = post_voucher(voucher)
    for e in entries:
        session.add(e)
    session.commit()

    assert len(entries) == 1
    entry = entries[0]
    # Phiếu chi TGNH trả nợ NCC: Nợ 331 / Có 1121
    assert entry.debit_acct == "331"
    assert entry.credit_acct == "1121"
    assert entry.amount == Decimal("500000")


def test_ledger_is_balanced_debit_equals_credit(db_session):
    session, company = db_session

    voucher = _make_receipt(company.id, total_amount=Decimal("2500000"))
    session.add(voucher)
    session.commit()
    session.refresh(voucher)

    entries = post_voucher(voucher)  # post_voucher tự validate cân đối, không raise là pass
    total_amount = sum(e.amount for e in entries)
    assert total_amount == voucher.total_amount


def test_unknown_txn_kind_raises_accounting_error(db_session):
    session, company = db_session

    voucher = _make_receipt(company.id, txn_kind="KHONG_TON_TAI")
    session.add(voucher)
    session.commit()
    session.refresh(voucher)

    with pytest.raises(AccountingError):
        post_voucher(voucher)


def test_all_configured_txn_kinds_resolve_to_known_accounts():
    # đảm bảo bảng map không trỏ tới TK rỗng/None
    for txn_kind, acct in TXN_KIND_ACCOUNT_MAP.items():
        assert acct, f"txn_kind {txn_kind} thiếu tài khoản đối ứng"
