from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Enum as SqlEnum, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    department = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        SqlEnum(UserRole),
        default=UserRole.EMPLOYEE,
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    attendances = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="employee", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="employee", cascade="all, delete-orphan")
