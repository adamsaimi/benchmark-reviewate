"""
Database connection and session management.

This module handles database connectivity, session creation,
and provides utilities for database operations.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from benchmark.config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using them
    pool_size=5,
    max_overflow=10,
    echo=False  # Set to True for SQL logging during development
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    This function is used as a FastAPI dependency to inject
    database sessions into route handlers. The session is automatically
    closed after use, regardless of success or failure.
    
    Yields:
        Database session that is automatically closed after use
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Rollback is handled in service layer, but we ensure cleanup here
        db.rollback()
        raise
    finally:
        db.close()
