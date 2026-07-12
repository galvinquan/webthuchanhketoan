from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Numeric
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class LedgerEntry(Base):
    __tablename__ = "ledger_entry"

    id = Column(Integer, primary_key=True, index=True)

    voucher_id = Column(
        Integer,
        ForeignKey("voucher.id"),
        nullable=False
    )

    company_id = Column(
        Integer,
        ForeignKey("company.id"),
        nullable=False
    )

    posting_date = Column(
        Date,
        nullable=False
    )

    narration = Column(
        String(500)
    )

    debit_acct = Column(
        String(10),
        ForeignKey("account.number"),
        nullable=False
    )

    credit_acct = Column(
        String(10),
        ForeignKey("account.number"),
        nullable=False
    )

    amount = Column(
        Numeric(18, 0),
        nullable=False
    )

    partner_id = Column(
        Integer,
        ForeignKey("partner.id")
    )

    voucher = relationship(
    "Voucher",
    back_populates="ledger_entries"
)

    company = relationship(
    "Company",
    back_populates="ledger_entries"
)

    partner = relationship(
    "Partner",
    back_populates="ledger_entries"
)

    debit_account = relationship(
        "Account",
        foreign_keys=[debit_acct]
    )

    credit_account = relationship(
        "Account",
        foreign_keys=[credit_acct]
    )