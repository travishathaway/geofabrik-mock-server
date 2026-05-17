import importlib.resources
import json
from pathlib import Path


def get_regions_path() -> Path:
    ref = importlib.resources.files("geofabrik_mock_server") / "regions.json"
    # In editable installs the traversable is already a real path; convert it.
    with importlib.resources.as_file(ref) as p:
        return p


def load_manifest() -> list[dict]:
    path = get_regions_path()
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_manifest(regions: list[dict]) -> None:
    path = get_regions_path()
    path.write_text(json.dumps(regions, indent=2) + "\n")


def find_region(regions: list[dict], region_id: str) -> dict | None:
    for r in regions:
        if r["id"] == region_id:
            return r
    return None
