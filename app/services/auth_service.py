from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import create_access_token, verify_password
from app.models.employee import Employee
from app.services.employee_service import get_employee_by_username


def authenticate_user(db: Session, username: str, password: str) -> tuple[str, Employee]:
    user = get_employee_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    access_token = create_access_token(subject=user.username)
    return access_token, user
