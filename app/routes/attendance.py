from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.employee import Employee
from app.schemas.attendance import AttendanceRead
from app.services.activity_log_service import create_log
from app.services.attendance_service import check_in, check_out, list_attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/check-in", response_model=AttendanceRead, status_code=status.HTTP_201_CREATED)
def employee_check_in(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    attendance = check_in(db, current_user)
    create_log(db, action="check_in", details="Employee checked in.", employee=current_user)
    return attendance


@router.post("/check-out", response_model=AttendanceRead, status_code=status.HTTP_200_OK)
def employee_check_out(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    attendance = check_out(db, current_user)
    create_log(
        db,
        action="check_out",
        details=f"Employee checked out with {attendance.total_hours} hours worked.",
        employee=current_user,
    )
    return attendance


@router.get("/me", response_model=list[AttendanceRead], status_code=status.HTTP_200_OK)
def get_my_attendance(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    return list_attendance(db, employee_id=current_user.id)


@router.get("", response_model=list[AttendanceRead], status_code=status.HTTP_200_OK)
def get_all_attendance(
    db: Session = Depends(get_db),
    _: Employee = Depends(require_admin),
):
    return list_attendance(db)
