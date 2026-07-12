from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Company(Base):
    __tablename__ = "company"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("app_user.id"),
        unique=True,
        nullable=False
    )

    name = Column(
        String(255),
        nullable=False
    )

    address = Column(String(500))

    tax_code = Column(String(14))

    student_name = Column(String(255))

    class_name = Column(String(100))

    period_from = Column(
        Date,
        nullable=False
    )

    period_to = Column(
        Date,
        nullable=False
    )

    user = relationship(
    "User",
    back_populates="company"
    )
    partners = relationship(
    "Partner",
    back_populates="company"
)

vouchers = relationship(
    "Voucher",
    back_populates="company"
)

opening_balances = relationship(
    "OpeningBalance",
    back_populates="company"
)

ledger_entries = relationship(
    "LedgerEntry",
    back_populates="company"
)