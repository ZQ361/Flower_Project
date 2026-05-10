"""Plant info service backed by SQLite."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..db.crud import get_plant_by_class_id, list_plants as list_plants_from_db, plant_to_dict


def list_plants(db: Session, query: str | None = None, limit: int | None = None) -> list[dict]:
    return list_plants_from_db(db, query=query, limit=limit)


def get_plant_detail(db: Session, class_id: int) -> dict | None:
    plant = get_plant_by_class_id(db, class_id)
    if plant is None:
        return None
    return plant_to_dict(plant)
