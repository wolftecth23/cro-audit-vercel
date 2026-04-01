from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.activity_log import ActivityLog
from app.models.employee import Employee
from app.schemas.activity_log import ActivityLogRead

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


@router.get("", response_model=list[ActivityLogRead], status_code=status.HTTP_200_OK)
def get_activity_logs(
    db: Session = Depends(get_db),
    _: Employee = Depends(require_admin),
):
    return db.query(ActivityLog).order_by(ActivityLog.created_at.desc()).all()
