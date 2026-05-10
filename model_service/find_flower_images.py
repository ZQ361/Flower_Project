"""Find Flowers-102 image paths by flower name.

Examples:
    C:/Users/zhouquan/miniconda3/envs/flower_project/python.exe model_service/find_flower_images.py
    C:/Users/zhouquan/miniconda3/envs/flower_project/python.exe model_service/find_flower_images.py rose
    C:/Users/zhouquan/miniconda3/envs/flower_project/python.exe model_service/find_flower_images.py "pink primrose" --limit 5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import scipy.io as sio


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = ROOT / "model_service" / "data" / "flowers-102"
DEFAULT_CATALOG_PATH = ROOT / "backend" / "app" / "data" / "flowers_102_zh.json"


def normalize(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())


def load_catalog(catalog_path: Path) -> list[dict]:
    with catalog_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def find_plant(catalog: list[dict], query: str) -> dict:
    normalized_query = normalize(query)

    exact_matches = [
        plant
        for plant in catalog
        if normalize(plant.get("name_en", "")) == normalized_query
        or normalize(plant.get("display_name", "")) == normalized_query
        or normalize(plant.get("name_cn", "")) == normalized_query
    ]
    if exact_matches:
        return exact_matches[0]

    partial_matches = [
        plant
        for plant in catalog
        if normalized_query in normalize(plant.get("name_en", ""))
        or normalized_query in normalize(plant.get("display_name", ""))
        or normalized_query in normalize(plant.get("name_cn", ""))
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]

    if partial_matches:
        names = ", ".join(f"{p['class_id']}:{p['name_en']}" for p in partial_matches)
        raise ValueError(f"Query is ambiguous. Matches: {names}")

    raise ValueError(f"No flower found for query: {query}")


def load_labels(labels_path: Path) -> list[int]:
    mat = sio.loadmat(labels_path)
    if "labels" not in mat:
        raise ValueError(f"No 'labels' variable found in {labels_path}")
    return [int(value) for value in mat["labels"].flatten()]


def image_path_for_index(jpg_dir: Path, image_index: int) -> Path:
    return jpg_dir / f"image_{image_index:05d}.jpg"


def has_jpg_files(jpg_dir: Path) -> bool | None:
    try:
        return any(jpg_dir.glob("*.jpg"))
    except PermissionError:
        return None


def path_exists(path: Path) -> bool | None:
    try:
        return path.exists()
    except PermissionError:
        return None


def find_images(
    *,
    query: str,
    catalog_path: Path,
    labels_path: Path,
    jpg_dir: Path,
    limit: int | None,
    existing_only: bool,
) -> tuple[dict, list[Path]]:
    catalog = load_catalog(catalog_path)
    plant = find_plant(catalog, query)

    # Oxford Flowers labels are 1-based; local class_id values are 0-based.
    target_label = int(plant["class_id"]) + 1
    labels = load_labels(labels_path)

    image_paths = [
        image_path_for_index(jpg_dir, index)
        for index, label in enumerate(labels, start=1)
        if label == target_label
    ]

    if existing_only:
        image_paths = [path for path in image_paths if path_exists(path) is True]

    if limit is not None:
        image_paths = image_paths[:limit]

    return plant, image_paths


def build_result(args: argparse.Namespace, plant: dict, image_paths: list[Path], jpg_dir: Path) -> dict:
    return {
        "query": args.query,
        "class_id": plant["class_id"],
        "flowers102_label": int(plant["class_id"]) + 1,
        "name_en": plant["name_en"],
        "display_name": plant.get("display_name"),
        "jpg_dir": str(jpg_dir),
        "count": len(image_paths),
        "paths": [str(path) for path in image_paths],
    }


def print_result(args: argparse.Namespace, result: dict, image_paths: list[Path], jpg_dir: Path) -> None:
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"{result['display_name']} / {result['name_en']}")
    print(f"class_id: {result['class_id']}")
    print(f"Flowers-102 label: {result['flowers102_label']}")
    print(f"matched images: {result['count']}")

    if not jpg_dir.exists():
        print(f"Warning: jpg directory does not exist: {jpg_dir}")
    else:
        jpg_status = has_jpg_files(jpg_dir)
        if jpg_status is False:
            print(f"Warning: jpg directory has no .jpg files: {jpg_dir}")
        elif jpg_status is None:
            print(f"Warning: no permission to list jpg directory; generated paths may still be correct: {jpg_dir}")

    for path in image_paths:
        exists = path_exists(path)
        exists_text = "exists" if exists is True else "missing" if exists is False else "unknown"
        print(f"{path} [{exists_text}]")


def run_query(args: argparse.Namespace) -> None:
    dataset_dir = args.dataset_dir.resolve()
    labels_path = dataset_dir / "imagelabels.mat"
    jpg_dir = dataset_dir / "jpg"

    plant, image_paths = find_images(
        query=args.query,
        catalog_path=args.catalog.resolve(),
        labels_path=labels_path,
        jpg_dir=jpg_dir,
        limit=args.limit,
        existing_only=args.existing_only,
    )
    result = build_result(args, plant, image_paths, jpg_dir)
    print_result(args, result, image_paths, jpg_dir)


def interactive_mode(args: argparse.Namespace) -> None:
    print("Flowers-102 image path lookup")
    print("Type an English or Chinese flower name, for example: rose / pink primrose / 玫瑰")
    print("Press Enter on an empty line to exit.")
    print()

    while True:
        query = input("Flower name> ").strip()
        if not query:
            break

        args.query = query
        try:
            run_query(args)
        except Exception as error:
            print(f"Error: {error}")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find Flowers-102 jpg paths by English or Chinese flower name.")
    parser.add_argument("query", nargs="?", help="Flower name, for example: rose, pink primrose, 玫瑰")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG_PATH)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--existing-only", action="store_true", help="Only print paths that currently exist on disk.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.query:
        interactive_mode(args)
        return
    run_query(args)


if __name__ == "__main__":
    main()
