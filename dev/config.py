from __future__ import annotations
"""Configuration loader for Vinayaka File Works.

Reads configuration from environment variables. For local development a .env file
may be used but MUST NOT be committed. In production, a managed secrets store
(e.g., AWS Secrets Manager) is required and should be documented in dev/docs.
"""
from dataclasses import dataclass
import os
from typing import Optional

try:
    # Optional for local dev convenience; respects .env only locally
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


@dataclass
class Config:
    app_env: str
    database_url: str
    redis_url: str
    secret_key: str
    storage_backend: str
    api_host: str
    api_port: int


def get_config() -> Config:
    app_env = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or "development").lower()
    database_url = os.getenv("DATABASE_URL")
    if app_env == "production" and not database_url:
        raise RuntimeError("DATABASE_URL must be configured when APP_ENV=production.")
    if not database_url:
        database_url = "sqlite:///dev.db"

    redis_url = os.getenv("REDIS_URL")
    if app_env == "production" and not redis_url:
        raise RuntimeError("REDIS_URL must be configured when APP_ENV=production.")
    if not redis_url:
        redis_url = "redis://localhost:6379/0"

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is not set. Configure the app with environment variables or a secret manager.")

    storage_backend = os.getenv("STORAGE_BACKEND", "local")
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))

    return Config(
        app_env=app_env,
        database_url=database_url,
        redis_url=redis_url,
        secret_key=secret_key,
        storage_backend=storage_backend,
        api_host=api_host,
        api_port=api_port,
    )
