from pathlib import Path

from geofabrik_mock_server.core.server import _mime_for


def test_mime_pbf():
    assert _mime_for(Path("monaco-latest.osm.pbf")) == "application/x-protobuf"


def test_mime_osc_gz():
    assert _mime_for(Path("000/001/002.osc.gz")) == "application/octet-stream"


def test_mime_json():
    assert _mime_for(Path("index-v1.json")) == "application/json"


def test_mime_state_txt():
    assert _mime_for(Path("state.txt")) == "text/plain"


def test_mime_unknown_extension():
    assert _mime_for(Path("somefile.xyz")) == "application/octet-stream"
