from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.task import TaskStatus


class TaskAssign(BaseModel):
    employee_id: int
    title: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = None
    project_name: str = Field(..., min_length=2, max_length=150)
    estimated_hours: float = Field(..., ge=0)
    due_date: Optional[date] = None


class TaskProgressUpdate(BaseModel):
    status: TaskStatus
    worked_hours: Optional[float] = Field(default=None, ge=0)


class TaskRead(BaseModel):
    id: int
    employee_id: int
    title: str
    description: Optional[str]
    project_name: str
    estimated_hours: float
    worked_hours: float
    due_date: Optional[date]
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
