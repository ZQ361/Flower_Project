"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from ..core.settings import BACKEND_NAME, DEFAULT_MODEL_NAME, DATABASE_PATH
from ..schemas import HealthResponse


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=BACKEND_NAME,
        data={
            "default_model_name": DEFAULT_MODEL_NAME,
            "storage": "sqlite",
            "database_path": str(DATABASE_PATH),
        },
    )
