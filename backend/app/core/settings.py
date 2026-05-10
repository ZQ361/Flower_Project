"""Backend runtime settings."""

from __future__ import annotations

import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"
BACKEND_DATA_DIR = BACKEND_DIR / "data"
MODEL_SERVICE_DIR = ROOT_DIR / "model_service"

DEFAULT_MODEL_NAME = "efficientnet_b0"
DEFAULT_CHECKPOINT_PATH = (
    MODEL_SERVICE_DIR / "checkpoints" / f"{DEFAULT_MODEL_NAME}_flowers102_final.pth"
)
FIGURES_DIR = MODEL_SERVICE_DIR / "log" / "figures"
BACKEND_NAME = "flower-recognition-backend"

DATABASE_PATH = BACKEND_DATA_DIR / "flower.sqlite3"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"
SECRET_KEY = os.getenv("FLOWER_SECRET_KEY", "flower-dev-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

BAILIAN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
BAILIAN_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)
BAILIAN_MODEL_NAME = os.getenv("DASHSCOPE_MODEL_NAME", "qwen3-max")
BAILIAN_TIMEOUT_SECONDS = float(os.getenv("DASHSCOPE_TIMEOUT_SECONDS", "30"))
RAG_RECENT_TURNS = int(os.getenv("RAG_RECENT_TURNS", "4"))
