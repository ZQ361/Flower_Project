"""Recognition history business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ..db.crud import create_recognition_history, list_user_history, remove_user_history_item


def record_history(
    db: Session,
    *,
    user_id: int | None,
    plant_id: int | None,
    image_name: str | None,
    image_path: str | None,
    pred_class: int,
    pred_name: str,
    confidence: float,
    top3: list[dict],
    source: str = "web",
):
    return create_recognition_history(
        db,
        user_id=user_id,
        plant_id=plant_id,
        image_name=image_name,
        image_path=image_path,
        pred_class=pred_class,
        pred_name=pred_name,
        confidence=confidence,
        top3=top3,
        source=source,
    )


def list_history_items(db: Session, *, user_id: int, limit: int | None = None):
    return list_user_history(db, user_id, limit=limit)


def delete_history_item(db: Session, *, user_id: int, history_id: int) -> bool:
    return remove_user_history_item(db, user_id=user_id, history_id=history_id)
