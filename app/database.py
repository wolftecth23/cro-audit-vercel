import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DEFAULT_SQLITE_FALLBACK_URL = (
    "sqlite:////tmp/employee_tracking.db"
    if os.getenv("VERCEL")
    else "sqlite:///./employee_tracking.db"
)

PRIMARY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:password@localhost:3306/employee_tracking",
)
SQLITE_FALLBACK_URL = os.getenv("SQLITE_FALLBACK_URL", DEFAULT_SQLITE_FALLBACK_URL)
ENABLE_SQLITE_FALLBACK = os.getenv("ENABLE_SQLITE_FALLBACK", "true").strip().lower() in {"1", "true", "yes", "on"}


def _engine_kwargs(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "future": True,
        }
    return {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "future": True,
    }


def _build_engine(database_url: str):
    return create_engine(database_url, **_engine_kwargs(database_url))


def _resolve_database_url() -> str:
    if not ENABLE_SQLITE_FALLBACK or PRIMARY_DATABASE_URL.startswith("sqlite"):
        return PRIMARY_DATABASE_URL

    try:
        probe_engine = _build_engine(PRIMARY_DATABASE_URL)
        with probe_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        probe_engine.dispose()
        return PRIMARY_DATABASE_URL
    except SQLAlchemyError:
        return SQLITE_FALLBACK_URL


DATABASE_URL = _resolve_database_url()
engine = _build_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
