"""Database seed helpers."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..services.catalog import get_catalog
from .models import PlantSpecies


def _catalog_record_to_model(record: dict) -> PlantSpecies:
    return PlantSpecies(
        class_id=record["class_id"],
        name_en=record["name_en"],
        name_cn=record.get("name_cn"),
        display_name=record["display_name"],
        description=record["description"],
        morphology=record.get("morphology"),
        habitat=record.get("habitat"),
        care_tips=list(record.get("care_tips", [])),
        flower_language=record.get("flower_language", ""),
        season=record.get("season", ""),
        distribution=record.get("distribution"),
        tags=list(record.get("tags", [])),
        source=record.get("source", "auto-generated"),
    )


def _apply_record_to_model(model: PlantSpecies, record: dict) -> None:
    model.name_en = record["name_en"]
    model.name_cn = record.get("name_cn")
    model.display_name = record["display_name"]
    model.description = record["description"]
    model.morphology = record.get("morphology")
    model.habitat = record.get("habitat")
    model.care_tips = list(record.get("care_tips", []))
    model.flower_language = record.get("flower_language", "")
    model.season = record.get("season", "")
    model.distribution = record.get("distribution")
    model.tags = list(record.get("tags", []))
    model.source = record.get("source", "auto-generated")


def seed_reference_data(db: Session) -> None:
    existing = {
        item.class_id: item
        for item in db.scalars(select(PlantSpecies)).all()
    }

    changed = False
    for record in get_catalog():
        model = existing.get(record["class_id"])
        if model is None:
            db.add(_catalog_record_to_model(record))
            changed = True
            continue

        _apply_record_to_model(model, record)
        changed = True

    if changed:
        db.commit()
