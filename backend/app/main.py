"""FastAPI application entry for the first-stage flower platform."""
# """
# uvicorn backend.app.main:app --reload
# """


from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.session import init_database
from .routers.auth import router as auth_router
from .routers.favorites import router as favorites_router
from .routers.health import router as health_router
from .routers.history import router as history_router
from .routers.rag import router as rag_router
from .routers.plants import router as plants_router
from .routers.recognition import router as recognition_router


app = FastAPI(title="Flower Recognition and Science Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(plants_router, prefix="/api")
app.include_router(recognition_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(favorites_router, prefix="/api")
app.include_router(history_router, prefix="/api")
app.include_router(rag_router, prefix="/api")


@app.on_event("startup")
def startup_event() -> None:
    init_database()
