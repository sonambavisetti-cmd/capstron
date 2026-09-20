from __future__ import annotations
"""Database helper: engine, Base, and session maker.

This module keeps configuration minimal for local dev. Use DATABASE_URL env var
in production (e.g., postgres). For SQLite a local file `dev.db` will be used.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///dev.db")

# For SQLite, enable check_same_thread if using threads in dev
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def init_db():
    """Create tables using models' metadata without destructive resets in production.

    Local SQLite development may recreate tables for test isolation; production
    deployments should rely on Alembic migrations instead of drop_all().
    """
    # Import models to register them with SQLAlchemy's Base metadata
    import dev.models  # noqa: F401

    if os.getenv("APP_ENV", "development").lower() != "production":
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Done")
