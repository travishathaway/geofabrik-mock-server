import json
from pathlib import Path


def get_regions_path(config: str | None = None) -> Path:
    if config is not None:
        return Path(config)
    return Path(".") / "regions.json"


def load_manifest(config: str | None = None) -> list[dict]:
    path = get_regions_path(config)
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_manifest(regions: list[dict], config: str | None = None) -> None:
    path = get_regions_path(config)
    path.write_text(json.dumps(regions, indent=2) + "\n")


def find_region(regions: list[dict], region_id: str) -> dict | None:
    for r in regions:
        if r["id"] == region_id:
            return r
    return None
