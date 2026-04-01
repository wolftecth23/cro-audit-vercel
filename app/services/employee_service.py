from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models.employee import Employee, UserRole
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


def get_employee_by_id(db: Session, employee_id: int) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found.")
    return employee


def get_employee_by_username(db: Session, username: str) -> Employee | None:
    return db.query(Employee).filter(Employee.username == username).first()


def validate_employee_uniqueness(
    db: Session,
    username: str,
    email: str,
    exclude_id: int | None = None,
) -> None:
    username_query = db.query(Employee).filter(Employee.username == username)
    email_query = db.query(Employee).filter(Employee.email == email)

    if exclude_id is not None:
        username_query = username_query.filter(Employee.id != exclude_id)
        email_query = email_query.filter(Employee.id != exclude_id)

    if username_query.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists.")
    if email_query.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")


def create_employee(db: Session, payload: EmployeeCreate) -> Employee:
    validate_employee_uniqueness(db, payload.username, payload.email)
    employee = Employee(
        full_name=payload.full_name,
        email=payload.email,
        username=payload.username,
        department=payload.department,
        role=payload.role,
        is_active=payload.is_active,
        password_hash=hash_password(payload.password),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(db: Session, employee: Employee, payload: EmployeeUpdate) -> Employee:
    updates = payload.model_dump(exclude_unset=True)

    if "username" in updates or "email" in updates:
        validate_employee_uniqueness(
            db,
            updates.get("username", employee.username),
            updates.get("email", employee.email),
            exclude_id=employee.id,
        )

    if "password" in updates:
        employee.password_hash = hash_password(updates.pop("password"))

    for field, value in updates.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    return employee


def delete_employee(db: Session, employee: Employee) -> None:
    db.delete(employee)
    db.commit()


def ensure_admin_user(
    db: Session,
    full_name: str,
    email: str,
    username: str,
    password: str,
) -> Employee | None:
    admin_exists = db.query(Employee).filter(Employee.role == UserRole.ADMIN).first()
    if admin_exists:
        return None

    employee = Employee(
        full_name=full_name,
        email=email,
        username=username,
        department="Administration",
        role=UserRole.ADMIN,
        is_active=True,
        password_hash=hash_password(password),
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee
