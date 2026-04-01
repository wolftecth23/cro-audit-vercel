from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.activity_log_service import create_log
from app.services.auth_service import authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    access_token, user = authenticate_user(db, payload.username, payload.password)
    create_log(db, action="login", details="User logged in successfully.", employee=user)
    return TokenResponse(access_token=access_token, user=user)
