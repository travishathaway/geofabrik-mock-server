from pathlib import Path

from geofabrik_mock_server.core.manifest import find_region, get_regions_path

_REGIONS = [
    {"id": "europe", "name": "Europe"},
    {"id": "andorra", "name": "Andorra"},
]


def test_find_region_found():
    result = find_region(_REGIONS, "andorra")
    assert result is not None
    assert result["id"] == "andorra"


def test_find_region_not_found():
    assert find_region(_REGIONS, "nonexistent") is None


def test_find_region_empty_list():
    assert find_region([], "andorra") is None


def test_get_regions_path_default():
    assert get_regions_path() == Path(".") / "regions.json"


def test_get_regions_path_custom():
    assert get_regions_path("/tmp/custom.json") == Path("/tmp/custom.json")
