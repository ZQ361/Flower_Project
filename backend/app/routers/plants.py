"""Plant catalog endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..schemas import PlantInfo, PlantListResponse
from ..services.plant_service import get_plant_detail, list_plants
from ..db.session import get_db


router = APIRouter(prefix="/plants", tags=["plants"])


@router.get("", response_model=PlantListResponse)
def read_plants(
    db: Session = Depends(get_db),
    query: str | None = Query(default=None, description="Search keyword"),
    limit: int | None = Query(default=None, ge=1, le=200),
) -> PlantListResponse:
    items = list_plants(db, query=query, limit=limit)
    return PlantListResponse(items=[PlantInfo(**item) for item in items], total=len(items))


@router.get("/{class_id}", response_model=PlantInfo)
def read_plant(class_id: int, db: Session = Depends(get_db)) -> PlantInfo:
    item = get_plant_detail(db, class_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Plant not found")
    return PlantInfo(**item)
