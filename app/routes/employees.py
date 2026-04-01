from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate
from app.services.activity_log_service import create_log
from app.services.employee_service import (
    create_employee,
    delete_employee,
    get_employee_by_id,
    update_employee,
)

router = APIRouter(prefix="/employees", tags=["Employees"])


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee_endpoint(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    admin: Employee = Depends(require_admin),
):
    employee = create_employee(db, payload)
    create_log(
        db,
        action="employee_created",
        details=f"Employee '{employee.username}' created by admin '{admin.username}'.",
        employee=admin,
    )
    return employee


@router.get("", response_model=list[EmployeeRead], status_code=status.HTTP_200_OK)
def list_employees(
    db: Session = Depends(get_db),
    _: Employee = Depends(require_admin),
):
    return db.query(Employee).order_by(Employee.created_at.desc()).all()


@router.get("/me", response_model=EmployeeRead, status_code=status.HTTP_200_OK)
def get_my_profile(current_user: Employee = Depends(get_current_user)):
    return current_user


@router.get("/{employee_id}", response_model=EmployeeRead, status_code=status.HTTP_200_OK)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    _: Employee = Depends(require_admin),
):
    return get_employee_by_id(db, employee_id)


@router.put("/{employee_id}", response_model=EmployeeRead, status_code=status.HTTP_200_OK)
def update_employee_endpoint(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    admin: Employee = Depends(require_admin),
):
    employee = get_employee_by_id(db, employee_id)
    updated_employee = update_employee(db, employee, payload)
    create_log(
        db,
        action="employee_updated",
        details=f"Employee '{updated_employee.username}' updated by admin '{admin.username}'.",
        employee=admin,
    )
    return updated_employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_endpoint(
    employee_id: int,
    db: Session = Depends(get_db),
    admin: Employee = Depends(require_admin),
):
    employee = get_employee_by_id(db, employee_id)
    username = employee.username
    delete_employee(db, employee)
    create_log(
        db,
        action="employee_deleted",
        details=f"Employee '{username}' deleted by admin '{admin.username}'.",
        employee=admin,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
