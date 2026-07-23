from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Enrollment(Base):
    __tablename__ = "enrollment"

    class_id = Column(
        Integer,
        ForeignKey("class_room.id"),
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("app_user.id"),
        primary_key=True
    )

    joined_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # "active" | "removed" (giữ lịch sử thay vì xóa cứng khi giáo viên gỡ SV khỏi lớp)
    status = Column(
        String(20),
        nullable=False,
        default="active"
    )

    classroom = relationship(
        "ClassRoom",
        back_populates="enrollments"
    )

    user = relationship(
        "User",
        back_populates="enrollments"
    )
