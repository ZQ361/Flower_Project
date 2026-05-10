"""Database engine and session helpers."""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.settings import BACKEND_DATA_DIR, DATABASE_URL
from .base import Base


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database() -> None:
    BACKEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    from .seed import seed_reference_data

    with SessionLocal() as db:
        seed_reference_data(db)
