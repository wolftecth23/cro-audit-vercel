from datetime import date, datetime
from enum import Enum

from sqlalchemy import Column, Date, DateTime, Enum as SqlEnum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    project_name = Column(String(150), nullable=False, index=True)
    estimated_hours = Column(Float, nullable=False, default=0)
    worked_hours = Column(Float, nullable=False, default=0)
    due_date = Column(Date, nullable=True)
    status = Column(
        SqlEnum(TaskStatus),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    employee = relationship("Employee", back_populates="tasks")
