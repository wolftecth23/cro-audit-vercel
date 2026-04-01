from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskAssign, TaskProgressUpdate
from app.services.employee_service import get_employee_by_id


def assign_task(db: Session, payload: TaskAssign) -> Task:
    get_employee_by_id(db, payload.employee_id)
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task_by_id(db: Session, task_id: int) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")
    return task


def list_tasks(db: Session, employee_id: int | None = None) -> list[Task]:
    query = db.query(Task).order_by(Task.created_at.desc())
    if employee_id is not None:
        query = query.filter(Task.employee_id == employee_id)
    return query.all()


def update_task_progress(db: Session, task: Task, payload: TaskProgressUpdate) -> Task:
    task.status = payload.status
    if payload.worked_hours is not None:
        task.worked_hours = payload.worked_hours
    db.commit()
    db.refresh(task)
    return task
