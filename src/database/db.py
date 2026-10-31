"""Database engine and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import DATABASE_URL


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


_engine_kwargs = {"future": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def init_db() -> None:
    """Create all registered database tables."""
    # Import models so SQLAlchemy registers their table metadata.
    from src.database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session():
    """Yield a database session and always close it."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
