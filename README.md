# Employee Tracking System Backend

Production-ready FastAPI backend for employee management, JWT authentication, attendance tracking, project task tracking, and activity logs.

## Folder Structure

```text
app/
├── auth/
│   ├── __init__.py
│   ├── dependencies.py
│   └── security.py
├── models/
│   ├── __init__.py
│   ├── activity_log.py
│   ├── attendance.py
│   ├── employee.py
│   └── task.py
├── routes/
│   ├── __init__.py
│   ├── activity_logs.py
│   ├── attendance.py
│   ├── auth.py
│   ├── employees.py
│   └── tasks.py
├── schemas/
│   ├── __init__.py
│   ├── activity_log.py
│   ├── attendance.py
│   ├── auth.py
│   ├── employee.py
│   └── task.py
├── services/
│   ├── __init__.py
│   ├── activity_log_service.py
│   ├── attendance_service.py
│   ├── auth_service.py
│   ├── employee_service.py
│   └── task_service.py
├── utils/
│   ├── __init__.py
│   └── time.py
├── __init__.py
├── database.py
└── main.py
requirements.txt
.env.example
README.md
```

## Features

- JWT login with role-based access for `admin` and `employee`
- Admin-managed employee CRUD
- Employee profile endpoint
- Check-in/check-out attendance with automatic total hours calculation
- Task assignment by project with estimated hours and worked hours tracking
- Task status updates: `pending`, `in_progress`, `done`
- Activity logs for login, attendance, employee changes, and task updates

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv venv
.\venv\Scripts\activate
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create a MySQL database.

```sql
CREATE DATABASE employee_tracking;
```

4. Copy `.env.example` to `.env` and update database credentials.

```powershell
Copy-Item .env.example .env
```

5. Start the server.

```powershell
uvicorn app.main:app --reload
```

6. Open Swagger UI.

`http://127.0.0.1:8000/docs`

On first startup, the app creates a default admin from the `DEFAULT_ADMIN_*` values in `.env` if no admin exists yet.

## Authentication Flow

- Admin creates employees using `POST /api/v1/employees`
- Employees log in using `POST /api/v1/auth/login`
- Use the returned bearer token in secured routes

## Example API Requests

### 1. Login

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"Admin@123\"}"
```

### 2. Create Employee

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/employees" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"full_name\":\"John Doe\",\"email\":\"john@example.com\",\"username\":\"john\",\"department\":\"Engineering\",\"role\":\"employee\",\"is_active\":true,\"password\":\"StrongPass123\"}"
```

### 3. Check In

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/attendance/check-in" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>"
```

### 4. Check Out

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/attendance/check-out" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>"
```

### 5. Assign Task

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/tasks" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"employee_id\":2,\"title\":\"Build report API\",\"description\":\"Create project summary endpoint\",\"project_name\":\"Employee Portal\",\"estimated_hours\":12,\"due_date\":\"2026-03-30\"}"
```

### 6. Update Task Progress

```bash
curl -X PATCH "http://127.0.0.1:8000/api/v1/tasks/1/progress" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>" \
  -H "Content-Type: application/json" \
  -d "{\"status\":\"in_progress\",\"worked_hours\":6.5}"
```

### 7. View My Tasks

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/tasks/me" \
  -H "Authorization: Bearer <EMPLOYEE_TOKEN>"
```

### 8. View Activity Logs

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/activity-logs" \
  -H "Authorization: Bearer <ADMIN_TOKEN>"
```

## Production Notes

- Replace `Base.metadata.create_all()` with Alembic migrations for production deployments.
- Restrict CORS origins to trusted frontend domains.
- Store a long random `SECRET_KEY` in environment variables.
- Run behind a production ASGI server and reverse proxy.
