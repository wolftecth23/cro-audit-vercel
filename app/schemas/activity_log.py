from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ActivityLogRead(BaseModel):
    id: int
    employee_id: Optional[int]
    action: str
    details: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
