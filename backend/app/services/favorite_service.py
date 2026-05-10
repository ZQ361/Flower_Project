"""Favorite business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..db.crud import add_favorite, get_plant_by_id, list_user_favorites, remove_favorite


def add_user_favorite(db: Session, *, user_id: int, plant_id: int, note: str | None = None):
    plant = get_plant_by_id(db, plant_id)
    if plant is None:
        raise ValueError("Plant not found")
    return add_favorite(db, user_id=user_id, plant_id=plant.id, note=note)


def list_user_favorite_items(db: Session, *, user_id: int):
    return list_user_favorites(db, user_id)


def delete_user_favorite(db: Session, *, user_id: int, plant_id: int) -> bool:
    return remove_favorite(db, user_id=user_id, plant_id=plant_id)
