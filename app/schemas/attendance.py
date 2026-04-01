from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class AttendanceRead(BaseModel):
    id: int
    employee_id: int
    attendance_date: date
    check_in_time: datetime
    check_out_time: Optional[datetime]
    total_hours: Optional[float]
    created_at: datetime

    class Config:
        orm_mode = True
