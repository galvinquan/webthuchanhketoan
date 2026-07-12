from sqlalchemy import Column, Integer, String, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.db.database import Base


class OpeningBalance(Base):
    __tablename__ = "opening_balance"

    company_id = Column(
        Integer,
        ForeignKey("company.id"),
        primary_key=True
    )

    account_number = Column(
        String(10),
        ForeignKey("account.number"),
        primary_key=True
    )

    partner_id = Column(
        Integer,
        ForeignKey("partner.id"),
        primary_key=True,
        nullable=True
    )

    debit = Column(
        Numeric(18, 0),
        nullable=False,
        default=0
    )

    credit = Column(
        Numeric(18, 0),
        nullable=False,
        default=0
    )

    company = relationship(
    "Company",
    back_populates="opening_balances"
)

    account = relationship(
    "Account",
    back_populates="opening_balances"
)

    partner = relationship(
    "Partner",
    back_populates="opening_balances"
)