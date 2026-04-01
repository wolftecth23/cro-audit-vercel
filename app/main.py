import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine
from app.routes import activity_logs, attendance, auth, cro, employees, tasks
from app.services.activity_log_service import create_log
from app.services.employee_service import ensure_admin_user

WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_user = ensure_admin_user(
            db=db,
            full_name=os.getenv("DEFAULT_ADMIN_FULL_NAME", "System Administrator"),
            email=os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com"),
            username=os.getenv("DEFAULT_ADMIN_USERNAME", "admin"),
            password=os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123"),
        )
        if admin_user:
            create_log(db, action="bootstrap_admin_created", details="Default admin account created.", employee=admin_user)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Employee Tracking System API",
    description="Backend API for employee management, attendance, task tracking, and activity logs.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(attendance.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(activity_logs.router, prefix="/api/v1")
app.include_router(cro.router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


@app.get("/", tags=["Health"])
def root():
    return {"message": "Employee Tracking System API is running."}


@app.get("/cro-audit", include_in_schema=False)
def cro_audit_page():
    return FileResponse(WEB_DIR / "index.html")
