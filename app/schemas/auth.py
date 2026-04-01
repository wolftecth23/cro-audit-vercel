from pydantic import BaseModel

from app.schemas.employee import EmployeeRead


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: EmployeeRead

    class Config:
        orm_mode = True
