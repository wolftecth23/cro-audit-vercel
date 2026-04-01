from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.attendance import Attendance
from app.models.employee import Employee
from app.utils.time import calculate_hours


def get_employee_open_attendance(db: Session, employee_id: int) -> Attendance | None:
    return (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == employee_id,
            Attendance.check_out_time.is_(None),
        )
        .order_by(Attendance.check_in_time.desc())
        .first()
    )


def check_in(db: Session, employee: Employee) -> Attendance:
    open_attendance = get_employee_open_attendance(db, employee.id)
    if open_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active check-in.",
        )

    now = datetime.utcnow()
    attendance = Attendance(
        employee_id=employee.id,
        attendance_date=now.date(),
        check_in_time=now,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def check_out(db: Session, employee: Employee) -> Attendance:
    attendance = get_employee_open_attendance(db, employee.id)
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active check-in found.",
        )

    now = datetime.utcnow()
    attendance.check_out_time = now
    attendance.total_hours = calculate_hours(attendance.check_in_time, now)
    db.commit()
    db.refresh(attendance)
    return attendance


def list_attendance(db: Session, employee_id: int | None = None) -> list[Attendance]:
    query = db.query(Attendance).order_by(Attendance.check_in_time.desc())
    if employee_id is not None:
        query = query.filter(Attendance.employee_id == employee_id)
    return query.all()
