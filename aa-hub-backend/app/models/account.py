from sqlalchemy import Column, String, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class Account(Base):
    __tablename__ = "account"

    # Số hiệu tài khoản (1111, 1121, 131, ...)
    number = Column(
        String(10),
        primary_key=True
    )

    # Tên tài khoản
    name = Column(
        String(255),
        nullable=False
    )

    # Cấp tài khoản (1, 2, 3)
    level = Column(
        SmallInteger,
        nullable=False
    )

    # Tài khoản cha
    parent_number = Column(
        String(10),
        ForeignKey("account.number"),
        nullable=True
    )

    # Loại tài khoản (1 -> 9)
    acct_class = Column(
        SmallInteger,
        nullable=False
    )

    # DEBIT | CREDIT | DUAL
    balance_nature = Column(
        String(10),
        nullable=False
    )

    # Quan hệ tự tham chiếu
    parent = relationship(
        "Account",
        remote_side=[number]
    )
    opening_balances = relationship(
    "OpeningBalance",
    back_populates="account"
)