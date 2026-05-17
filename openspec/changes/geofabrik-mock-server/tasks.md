# Tasks: Geofabrik Mock Server

## 1. Fix existing bugs and update pyproject.toml

- [x] In `pyproject.toml`: change `packages = ["src/pg_helper"]` to `packages = ["src/geofabrik_mock_server"]`
- [x] In `pyproject.toml`: add `dependencies = ["click", "flask", "requests"]`
- [x] In `pyproject.toml`: add click, flask, requests to `[tool.pixi.dependencies]`
- [x] In `cli.py`: add `import sys` at the top
- [x] Add `.gitignore` rules to exclude `data/` contents but keep `.gitkeep`

## 2. Create package data skeleton

- [x] Create `src/geofabrik_mock_server/regions.json` with empty list `[]`
- [x] Create `src/geofabrik_mock_server/data/.gitkeep`
- [x] Create `src/geofabrik_mock_server/commands/__init__.py`
- [x] Create `src/geofabrik_mock_server/core/__init__.py`

## 3. Implement `core/manifest.py` ✓

Functions:
- `get_regions_path() -> Path`: resolves `regions.json` via `importlib.resources`
- `load_manifest() -> list[dict]`: reads and parses regions.json
- `save_manifest(regions: list[dict]) -> None`: writes regions.json
- `find_region(regions: list, region_id: str) -> dict | None`

## 4. Implement `core/geofabrik.py` ✓

Functions:
- `fetch_index() -> dict`: GET `https://download.geofabrik.de/index-v1.json`
- `find_region_in_index(index: dict, region_id: str) -> dict | None`: searches features by `id`
- `seq_to_path(seq: int) -> str`: e.g. `4001 → "000/004/001"`
- `fetch_state_file(updates_url: str, seq: int | None) -> dict | None`: fetches and parses a state.txt (root if seq is None)
- `resolve_sequence_for_date(updates_url: str, target_date: date) -> int`: binary search
- `download_file(url: str, dest: Path) -> None`: streams download with progress
- `download_pbf(pbf_url: str, dest: Path) -> None`
- `download_updates(updates_url: str, start_seq: int, data_dir: Path, region_path: str) -> None`: downloads all `.osc.gz` and `.state.txt` files from `start_seq` to current

## 5. Implement `commands/add.py` ✓

```
gms add <region-id> [--date YYYY-MM-DD]
```

- Fetch Geofabrik index, find region by id (e.g. `europe/andorra`)
- Error if region not found or already in manifest
- Append entry to manifest with `pbf_url`, `updates_url`, `start_date` (if provided)
- Print confirmation

## 6. Implement `commands/remove.py` ✓

```
gms remove <region-id>
```

- Load manifest, find region, error if not found
- Remove from manifest, save
- Optionally delete local data (prompt user or accept `--yes` flag)

## 7. Implement `commands/download.py` ✓

```
gms download [--region <id>]
```

- Load manifest (optionally filter to one region)
- For each region:
  - Download PBF to `data/<continent>/<region>-latest.osm.pbf`
  - If `start_date` is set: resolve sequence, download update diffs
  - Copy root state.txt to `data/<path>/<region>-updates/state.txt`
- Generate `data/index-v1.json`: a GeoJSON FeatureCollection with only the manifest regions (geometry + urls filtered to pbf and updates only)

## 8. Implement `core/server.py` ✓

Flask app:
- `create_app(data_root: Path) -> Flask`
- Route `GET /index-v1.json`: reads and returns `data/index-v1.json`
- Route `GET /<path:filepath>`: resolves to `data_root / filepath`, returns file or 404
- All responses set appropriate Content-Type (application/x-protobuf for .pbf, application/octet-stream for .osc.gz, application/json for .json, text/plain for .txt)

## 9. Implement `commands/serve.py` ✓

```
gms serve [--port 8080] [--host 0.0.0.0]
```

- Resolve data root via `importlib.resources.files("geofabrik_mock_server") / "data"`
- Create Flask app and run it
- Print startup message with base URL

## 10. Wire up `cli.py` ✓

- Replace stub with Click group
- Register all four commands: add, remove, download, serve
- Entry point remains `gms = "geofabrik_mock_server.cli:main"`

## 11. Verify end-to-end ✓

- [x] `pip install -e .` succeeds (click, flask, requests installed)
- [x] `gms --help` shows all four commands
- [x] `gms add europe/andorra --date 2026-05-15` → regions.json updated
- [x] `gms remove europe/andorra --yes` → entry removed, local data deleted
- [x] `gms download` → PBF + update diffs present in data/
- [x] `gms serve` → `curl localhost:8081/europe/andorra-latest.osm.pbf` returns 200
- [x] `curl localhost:8081/index-v1.json` returns filtered GeoJSON (1 feature: andorra)
- [x] `curl localhost:8081/europe/andorra-updates/state.txt` returns state
- [x] `curl localhost:8081/europe/andorra-updates/000/004/787.osc.gz` returns 200
- [x] Missing path returns 404
