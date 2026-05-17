# Design: Geofabrik Mock Server

## Module Layout

```
src/geofabrik_mock_server/
  __init__.py
  cli.py                    ← Click group; registers all subcommands
  regions.json              ← committed manifest (importlib.resources-accessible)
  commands/
    __init__.py
    add.py
    remove.py
    download.py
    serve.py
  core/
    __init__.py
    manifest.py             ← regions.json CRUD
    geofabrik.py            ← HTTP client + date→sequence resolver
    server.py               ← Flask app
  data/                     ← gitignored (except .gitkeep); bundled in conda package
    .gitkeep
```

## Data Flow

```
Developer workflow:
  gms add europe/andorra --date 2024-01-01
    └─▶ writes to src/geofabrik_mock_server/regions.json

  gms download
    └─▶ reads regions.json
    └─▶ for each region:
          • GET <pbf_url> → data/europe/andorra-latest.osm.pbf
          • resolve_sequence(updates_url, start_date) → seq S
          • download seq S..N → data/europe/andorra-updates/000/.../NNN.osc.gz
    └─▶ writes data/index-v1.json (filtered GeoJSON)

  gms serve --port 8080
    └─▶ Flask serves data/ at Geofabrik-equivalent paths

conda build workflow:
  pip install -e .
  gms download          ← same command, populates data/
  pixi build            ← packages data/ alongside Python module
```

## regions.json Schema

Stored at `src/geofabrik_mock_server/regions.json`, committed to git.

```json
[
  {
    "id": "europe/andorra",
    "name": "Andorra",
    "pbf_url": "https://download.geofabrik.de/europe/andorra-latest.osm.pbf",
    "updates_url": "https://download.geofabrik.de/europe/andorra-updates",
    "start_date": "2024-01-01"
  }
]
```

`start_date` is optional; if omitted, only the PBF is downloaded (no update diffs).

## Date → Sequence Number Algorithm

Geofabrik replication state files live at:
```
<updates_url>/000/004/001.state.txt   (seq 4001)
<updates_url>/state.txt               (current state)
```

State file format:
```
#Sun Jan 07 00:00:00 UTC 2024
sequenceNumber=4001
timestamp=2024-01-07T00:00:00Z
```

Sequence → path conversion: zero-pad to 9 digits, split into 3×3 groups:
```python
def seq_to_path(seq: int) -> str:
    s = f"{seq:09d}"
    return f"{s[0:3]}/{s[3:6]}/{s[6:9]}"
```

Date resolution binary search:
```python
def resolve_sequence_for_date(updates_url, target_date):
    N = fetch_current_sequence(updates_url)          # from root state.txt
    lo, hi = 0, N
    while hi - lo > 1:
        mid = (lo + hi) // 2
        ts = fetch_sequence_timestamp(updates_url, mid)  # may 404 → skip
        if ts is None or ts > target_date:
            hi = mid
        else:
            lo = mid
    return lo
```

~log₂(N) HTTP requests (≈16–20 for most regions).

## HTTP Server Routes (Flask)

```python
@app.route("/index-v1.json")
def index():
    # Return filtered GeoJSON FeatureCollection from data/index-v1.json

@app.route("/<path:filepath>")
def serve_file(filepath):
    # Resolve to data/<filepath>; send_file or 404
```

Data root located via:
```python
data_root = importlib.resources.files("geofabrik_mock_server") / "data"
```

## gms download: update diff download

After finding start sequence `S` and current sequence `N`:
1. For each seq in `range(S, N+1)`:
   - Download `<seq>.osc.gz` → `data/<path>/<region>-updates/<000/000/001>.osc.gz`
   - Download `<seq>.state.txt` → same directory
2. Copy root `state.txt` to `data/<path>/<region>-updates/state.txt`
3. Generate `data/index-v1.json` from regions manifest using Geofabrik's real index shape

## pyproject.toml Changes

```toml
dependencies = ["click", "flask", "requests"]

[tool.hatch.build.targets.wheel]
packages = ["src/geofabrik_mock_server"]   # fix: was src/pg_helper
```

Also add to `[tool.pixi.dependencies]`:
```toml
click = "*"
flask = "*"
requests = "*"
```

## .gitignore Additions

```
src/geofabrik_mock_server/data/*
!src/geofabrik_mock_server/data/.gitkeep
```

## Bugs Fixed as Part of This Change

- `pyproject.toml`: `packages = ["src/pg_helper"]` → `["src/geofabrik_mock_server"]`
- `cli.py`: missing `import sys`
