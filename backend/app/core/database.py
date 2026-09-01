"""Database configuration and setup for DocuFiscal application."""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from .config import settings

# Create database engine
# For SQLite, disable same thread check to allow FastAPI async usage
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.

    Yields:
        Session: SQLAlchemy database session

    Note:
        Session is automatically closed after request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()