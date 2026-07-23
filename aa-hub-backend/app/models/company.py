from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Numeric, Text,
    ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Company(Base):
    """
    Đại diện cho 1 bài làm/doanh nghiệp giả định của 1 sinh viên cho 1 bài tập
    cụ thể (assignment) trong 1 lớp. 1 sinh viên có thể có nhiều Company vì có
    thể làm nhiều bài tập ở nhiều lớp khác nhau, nhưng chỉ 1 Company cho mỗi
    (user, assignment).
    """
    __tablename__ = "company"
    __table_args__ = (
        UniqueConstraint("user_id", "assignment_id", name="uq_company_user_assignment"),
    )

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("app_user.id"),
        nullable=False
    )

    assignment_id = Column(
        Integer,
        ForeignKey("assignment.id"),
        nullable=True   # nullable để tương thích dữ liệu cũ tạo trước khi có bài tập
    )

    name = Column(String(255), nullable=False)
    address = Column(String(500))
    tax_code = Column(String(14))
    student_name = Column(String(255))
    class_name = Column(String(100))
    period_from = Column(Date, nullable=False)
    period_to = Column(Date, nullable=False)

    # "in_progress" | "submitted" | "graded"
    status = Column(
        String(20),
        nullable=False,
        default="in_progress"
    )

    score = Column(Numeric(5, 2), nullable=True)
    feedback = Column(Text, nullable=True)

    graded_by = Column(
        Integer,
        ForeignKey("app_user.id"),
        nullable=True
    )

    graded_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship(
        "User",
        back_populates="companies",
        foreign_keys=[user_id]
    )

    grader = relationship(
        "User",
        foreign_keys=[graded_by]
    )

    assignment = relationship(
        "Assignment",
        back_populates="submissions"
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
