from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.employee import Employee
from app.models.employee import UserRole
from app.schemas.task import TaskAssign, TaskProgressUpdate, TaskRead
from app.services.activity_log_service import create_log
from app.services.task_service import assign_task, get_task_by_id, list_tasks, update_task_progress

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def assign_task_endpoint(
    payload: TaskAssign,
    db: Session = Depends(get_db),
    admin: Employee = Depends(require_admin),
):
    task = assign_task(db, payload)
    create_log(
        db,
        action="task_assigned",
        details=(
            f"Task '{task.title}' assigned to employee ID {task.employee_id} "
            f"for project '{task.project_name}'."
        ),
        employee=admin,
    )
    return task


@router.get("/me", response_model=list[TaskRead], status_code=status.HTTP_200_OK)
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    return list_tasks(db, employee_id=current_user.id)


@router.get("", response_model=list[TaskRead], status_code=status.HTTP_200_OK)
def get_all_tasks(
    db: Session = Depends(get_db),
    _: Employee = Depends(require_admin),
):
    return list_tasks(db)


@router.patch("/{task_id}/progress", response_model=TaskRead, status_code=status.HTTP_200_OK)
def update_task_progress_endpoint(
    task_id: int,
    payload: TaskProgressUpdate,
    db: Session = Depends(get_db),
    current_user: Employee = Depends(get_current_user),
):
    task = get_task_by_id(db, task_id)

    if current_user.role != UserRole.ADMIN and task.employee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this task.")

    updated_task = update_task_progress(db, task, payload)
    create_log(
        db,
        action="task_updated",
        details=(
            f"Task '{updated_task.title}' updated to '{updated_task.status.value}' "
            f"with worked hours {updated_task.worked_hours}."
        ),
        employee=current_user,
    )
    return updated_task
