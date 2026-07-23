from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "app_user"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(100),
        unique=True,
        nullable=False
    )

    password = Column(
        String(255),
        nullable=False
    )

    # "student" | "teacher"
    role = Column(
        String(20),
        nullable=False,
        default="student"
    )

    # 1 user có thể có nhiều Company vì mỗi bài tập nộp -> 1 company riêng
    companies = relationship(
        "Company",
        back_populates="user",
        foreign_keys="Company.user_id"
    )

    # Các lớp mà user này là chủ (đã tạo). Quyền đồng-giáo-viên xem ClassTeacher.
    classes_owned = relationship(
        "ClassRoom",
        back_populates="teacher",
        foreign_keys="ClassRoom.teacher_id"
    )

    # Các lớp mà user này tham gia với tư cách sinh viên
    enrollments = relationship(
        "Enrollment",
        back_populates="user",
        cascade="all, delete-orphan"
    )
