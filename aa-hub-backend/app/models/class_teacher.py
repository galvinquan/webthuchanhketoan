from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class ClassTeacher(Base):
    """
    Gán giáo viên phụ trách 1 lớp. Giáo viên tạo lớp mặc định có role="owner";
    owner có thể assign thêm giáo viên khác (role="co_teacher") vào cùng lớp.
    """
    __tablename__ = "class_teacher"

    class_id = Column(
        Integer,
        ForeignKey("class_room.id"),
        primary_key=True
    )

    teacher_id = Column(
        Integer,
        ForeignKey("app_user.id"),
        primary_key=True
    )

    # "owner" | "co_teacher"
    role = Column(
        String(20),
        nullable=False,
        default="co_teacher"
    )

    added_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    classroom = relationship(
        "ClassRoom",
        back_populates="class_teachers"
    )

    teacher = relationship(
        "User",
        foreign_keys=[teacher_id]
    )
