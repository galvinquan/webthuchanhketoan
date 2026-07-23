from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Assignment(Base):
    __tablename__ = "assignment"

    id = Column(Integer, primary_key=True, index=True)

    class_id = Column(
        Integer,
        ForeignKey("class_room.id"),
        nullable=False
    )

    title = Column(String(255), nullable=False)

    description = Column(Text)

    due_date = Column(Date, nullable=True)

    created_by = Column(
        Integer,
        ForeignKey("app_user.id"),
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    classroom = relationship(
        "ClassRoom",
        back_populates="assignments"
    )

    creator = relationship(
        "User",
        foreign_keys=[created_by]
    )

    submissions = relationship(
        "Company",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )
