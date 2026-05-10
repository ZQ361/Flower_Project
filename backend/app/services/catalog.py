"""Plant catalog loaded from JSON data."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "flowers_102_zh.json"


def _normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    name_en = str(record.get("name_en", "")).strip()
    name_cn = str(record.get("name_cn") or name_en).strip()
    display_name = str(record.get("display_name") or name_cn or name_en).strip()

    return {
        "class_id": int(record["class_id"]),
        "name_en": name_en,
        "name_cn": name_cn,
        "display_name": display_name,
        "description": str(record.get("description") or "").strip(),
        "morphology": record.get("morphology"),
        "habitat": record.get("habitat"),
        "care_tips": list(record.get("care_tips") or []),
        "flower_language": str(record.get("flower_language") or "").strip(),
        "season": str(record.get("season") or "").strip(),
        "distribution": record.get("distribution"),
        "tags": list(record.get("tags") or []),
        "source": str(record.get("source") or "json-catalog").strip(),
    }


def _load_catalog() -> list[dict[str, Any]]:
    if not CATALOG_PATH.exists():
        return []

    with CATALOG_PATH.open("r", encoding="utf-8") as handle:
        raw_catalog = json.load(handle)

    catalog = [_normalize_record(item) for item in raw_catalog]
    catalog.sort(key=lambda item: item["class_id"])
    return catalog


@lru_cache(maxsize=1)
def get_catalog() -> list[dict[str, Any]]:
    return _load_catalog()


def get_plant_by_class_id(class_id: int) -> dict[str, Any] | None:
    catalog = get_catalog()
    if class_id < 0 or class_id >= len(catalog):
        return None
    return catalog[class_id]


def search_plants(query: str) -> list[dict[str, Any]]:
    normalized = query.strip().lower()
    if not normalized:
        return get_catalog()

    results: list[dict[str, Any]] = []
    for plant in get_catalog():
        haystack = " ".join(
            [
                str(plant["class_id"]),
                plant["name_en"],
                plant["name_cn"],
                plant["display_name"],
                plant["description"],
                plant["flower_language"],
                plant["season"],
                " ".join(plant["tags"]),
            ]
        ).lower()
        if normalized in haystack:
            results.append(plant)
    return results
