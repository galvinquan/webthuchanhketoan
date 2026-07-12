from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Numeric,
    SmallInteger
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Voucher(Base):
    __tablename__ = "voucher"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(
        Integer,
        ForeignKey("company.id"),
        nullable=False
    )

    voucher_no = Column(
        String(20),
        nullable=False
    )

    voucher_type = Column(
        String(10),
        nullable=False
    )

    cash_source = Column(
        String(3),
        nullable=False
    )

    txn_kind = Column(
        String(20),
        nullable=False
    )

    partner_id = Column(
        Integer,
        ForeignKey("partner.id")
    )

    reason = Column(
        String(500)
    )

    voucher_date = Column(
        Date,
        nullable=False
    )

    posting_date = Column(
        Date,
        nullable=False
    )

    attached_docs = Column(
        SmallInteger,
        default=0
    )

    total_amount = Column(
        Numeric(18,0),
        nullable=False
    )

    company = relationship(
    "Company",
    back_populates="vouchers"
)

    partner = relationship(
    "Partner",
    back_populates="vouchers"
)
    ledger_entries = relationship(
    "LedgerEntry",
    back_populates="voucher",
    cascade="all, delete-orphan"
)