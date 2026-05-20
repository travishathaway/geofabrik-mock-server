from datetime import date

from geofabrik_mock_server.core.geofabrik import (
    _parse_state_body,
    _state_timestamp,
    build_dated_pbf_url,
    find_region_in_index,
    seq_to_path,
)


def test_seq_to_path_basic():
    assert seq_to_path(123456789) == "123/456/789"


def test_seq_to_path_zero_padded():
    assert seq_to_path(1) == "000/000/001"


def test_seq_to_path_boundary():
    assert seq_to_path(999999999) == "999/999/999"


def test_build_dated_pbf_url():
    url = "https://download.geofabrik.de/europe/monaco-latest.osm.pbf"
    assert build_dated_pbf_url(url, date(2026, 5, 12)) == (
        "https://download.geofabrik.de/europe/monaco-260512.osm.pbf"
    )


def test_build_dated_pbf_url_zero_padded_month():
    url = "https://download.geofabrik.de/africa/senegal-and-gambia-latest.osm.pbf"
    assert build_dated_pbf_url(url, date(2026, 1, 5)) == (
        "https://download.geofabrik.de/africa/senegal-and-gambia-260105.osm.pbf"
    )


def test_parse_state_body_basic():
    text = "sequenceNumber=12345\ntimestamp=2026-01-01T00\\:00\\:00Z\n"
    result = _parse_state_body(text)
    assert result is not None
    assert result["sequenceNumber"] == "12345"
    assert result["timestamp"] == "2026-01-01T00:00:00Z"


def test_parse_state_body_ignores_comments():
    text = "# this is a comment\nsequenceNumber=999\n"
    result = _parse_state_body(text)
    assert result is not None
    assert result["sequenceNumber"] == "999"
    assert len(result) == 1


def test_parse_state_body_missing_sequence_returns_none():
    assert _parse_state_body("timestamp=2026-01-01T00:00:00Z\n") is None


def test_parse_state_body_empty_returns_none():
    assert _parse_state_body("") is None


def test_state_timestamp_valid():
    assert _state_timestamp({"timestamp": "2026-05-12T00:00:00Z"}) == date(2026, 5, 12)


def test_state_timestamp_missing_key():
    assert _state_timestamp({}) is None


def test_state_timestamp_empty_string():
    assert _state_timestamp({"timestamp": ""}) is None


def test_state_timestamp_invalid_format():
    assert _state_timestamp({"timestamp": "not-a-date"}) is None


_SAMPLE_INDEX = {
    "features": [
        {"properties": {"id": "andorra", "parent": "europe"}},
        {"properties": {"id": "europe"}},
        {"properties": {"id": "monaco", "parent": "europe"}},
    ]
}


def test_find_region_in_index_found():
    result = find_region_in_index(_SAMPLE_INDEX, "andorra")
    assert result is not None
    assert result["properties"]["id"] == "andorra"


def test_find_region_in_index_not_found():
    assert find_region_in_index(_SAMPLE_INDEX, "nonexistent") is None


def test_find_region_in_index_empty_index():
    assert find_region_in_index({}, "andorra") is None
