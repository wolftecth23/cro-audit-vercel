from datetime import datetime
from typing import Union, Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.employee import UserRole


class EmployeeBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    department: Optional[str] = Field(default=None, max_length=100)
    role: UserRole = UserRole.EMPLOYEE
    is_active: bool = True

    class Config:
        orm_mode = True


class EmployeeCreate(EmployeeBase):
    password: str = Field(..., min_length=8, max_length=128)


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    department: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class EmployeeRead(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    username: str
    department: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
