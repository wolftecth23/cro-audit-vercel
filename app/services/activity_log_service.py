from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog
from app.models.employee import Employee


def create_log(
    db: Session,
    action: str,
    details: str | None = None,
    employee: Employee | None = None,
) -> ActivityLog:
    log = ActivityLog(
        employee_id=employee.id if employee else None,
        action=action,
        details=details,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
