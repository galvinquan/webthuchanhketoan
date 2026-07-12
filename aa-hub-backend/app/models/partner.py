from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Partner(Base):
    __tablename__ = "partner"

    id = Column(Integer, primary_key=True, index=True)

    company_id = Column(
        Integer,
        ForeignKey("company.id"),
        nullable=False
    )

    type = Column(
        String(10),
        nullable=False
    )

    code = Column(String(50))

    name = Column(
        String(255),
        nullable=False
    )

    address = Column(String(500))

    tax_code = Column(String(14))

    goods_name = Column(String(255))

    company = relationship(
    "Company",
    back_populates="partners"
    )
    vouchers = relationship(
    "Voucher",
    back_populates="partner"
)

opening_balances = relationship(
    "OpeningBalance",
    back_populates="partner"
)

ledger_entries = relationship(
    "LedgerEntry",
    back_populates="partner"
)