"""Lightweight DB adapter for the app package.

This module intentionally re-exports the project's existing DB helper (dev.db)
so application modules can import from `dev.app.db` without duplicating
connection logic. It also provides a small FastAPI-friendly dependency helper
(get_db) used by the API layer.
"""
from typing import Generator

from dev import db as core_db
from sqlalchemy.orm import Session

# Re-export main DB objects
engine = core_db.engine
SessionLocal = core_db.SessionLocal
Base = core_db.Base


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and ensure it is closed after use.

    Use as a FastAPI dependency:
        db = Depends(dev.app.db.get_db)
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
