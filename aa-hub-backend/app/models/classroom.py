import random
import string

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


def generate_join_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choices(alphabet, k=length))


class ClassRoom(Base):
    __tablename__ = "class_room"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(255), nullable=False)

    # Giáo viên tạo lớp (chủ lớp). Quyền chi tiết theo-giáo-viên nằm ở ClassTeacher.
    teacher_id = Column(
        Integer,
        ForeignKey("app_user.id"),
        nullable=False
    )

    join_code = Column(
        String(10),
        unique=True,
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    teacher = relationship(
        "User",
        back_populates="classes_owned",
        foreign_keys=[teacher_id]
    )

    enrollments = relationship(
        "Enrollment",
        back_populates="classroom",
        cascade="all, delete-orphan"
    )

    class_teachers = relationship(
        "ClassTeacher",
        back_populates="classroom",
        cascade="all, delete-orphan"
    )

    assignments = relationship(
        "Assignment",
        back_populates="classroom",
        cascade="all, delete-orphan"
    )
