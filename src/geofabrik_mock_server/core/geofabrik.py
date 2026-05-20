import hashlib
import shutil
from datetime import date, datetime
from pathlib import Path

import requests

GEOFABRIK_INDEX_URL = "https://download.geofabrik.de/index-v1.json"


def fetch_index() -> dict:
    resp = requests.get(GEOFABRIK_INDEX_URL, timeout=30)
    resp.raise_for_status()
    return resp.json()


def find_region_in_index(index: dict, region_id: str) -> dict | None:
    """Find a region by its path-style ID (e.g. 'europe/andorra' or 'andorra').

    Geofabrik's index uses short `id` values (e.g. 'andorra') with a `parent` field
    (e.g. 'europe'). A path-style input is resolved by matching the last segment against
    `id` and the preceding segment against `parent`.
    """
    for feature in index.get("features", []):
        props = feature.get("properties", {})
        if props.get("id") != region_id:
            continue
        return feature
    return None


def seq_to_path(seq: int) -> str:
    s = f"{seq:09d}"
    return f"{s[0:3]}/{s[3:6]}/{s[6:9]}"


def _parse_state_body(text: str) -> dict | None:
    result = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().replace("\\:", ":")
    if "sequenceNumber" not in result:
        return None
    return result


def fetch_state_file(updates_url: str, seq: int | None = None) -> dict | None:
    if seq is None:
        url = f"{updates_url}/state.txt"
    else:
        url = f"{updates_url}/{seq_to_path(seq)}.state.txt"
    try:
        resp = requests.get(url, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return _parse_state_body(resp.text)
    except requests.RequestException:
        return None


def _state_timestamp(state: dict) -> date | None:
    ts_str = state.get("timestamp", "")
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.date()
    except ValueError:
        return None


def resolve_sequence_for_date(updates_url: str, target_date: date) -> int:
    """Binary-search for the latest sequence whose timestamp <= target_date.

    404 responses mean the region's feed doesn't go that far back; we treat
    them as "search higher" so the result converges to the first available
    sequence when the target date predates the feed.
    """
    root_state = fetch_state_file(updates_url)
    if root_state is None:
        raise RuntimeError(f"Could not fetch state.txt from {updates_url}")
    n = int(root_state["sequenceNumber"])

    lo, hi = 0, n
    while hi - lo > 1:
        mid = (lo + hi) // 2
        state = fetch_state_file(updates_url, mid)
        if state is None:
            # Sequence not in feed yet — the region started later; go higher
            lo = mid
            continue
        ts = _state_timestamp(state)
        if ts is None or ts > target_date:
            hi = mid
        else:
            lo = mid

    # If lo is still in a 404 zone, walk forward to find the first real sequence
    if fetch_state_file(updates_url, lo) is None:
        for candidate in range(lo + 1, n + 1):
            if fetch_state_file(updates_url, candidate) is not None:
                return candidate
        return n  # nothing found; start from current

    return lo


def download_file(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=60) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            shutil.copyfileobj(resp.raw, f)


def build_dated_pbf_url(pbf_url: str, target_date: date) -> str:
    """Return the dated variant of a -latest.osm.pbf URL.

    'https://download.geofabrik.de/europe/monaco-latest.osm.pbf', date(2026, 5, 12)
    → 'https://download.geofabrik.de/europe/monaco-260512.osm.pbf'
    """
    date_str = target_date.strftime("%y%m%d")
    return pbf_url.replace("-latest.osm.pbf", f"-{date_str}.osm.pbf")


def _verify_md5(file_path: Path, md5_url: str) -> None:
    resp = requests.get(md5_url, timeout=15)
    resp.raise_for_status()
    # MD5 file format: "hash  filename" or just "hash"
    expected = resp.text.strip().split()[0]
    actual = hashlib.md5(file_path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(
            f"MD5 mismatch for {file_path.name}: expected {expected}, got {actual}"
        )


def download_pbf(pbf_url: str, dest: Path) -> None:
    print(f"  Downloading PBF: {pbf_url}")
    download_file(pbf_url, dest)
    md5_url = f"{pbf_url}.md5"
    print(f"  Verifying MD5…")
    _verify_md5(dest, md5_url)
    print(f"  MD5 OK — saved: {dest}")
    download_file(md5_url, Path(f"{dest}.md5"))


def download_pbf_for_date(pbf_url: str, target_date: date, dest: Path) -> None:
    """Download the dated PBF snapshot, verify its MD5, and save it as dest."""
    dated_url = build_dated_pbf_url(pbf_url, target_date)
    md5_url = dated_url + ".md5"
    print(f"  Downloading PBF: {dated_url}")
    download_file(dated_url, dest)
    print(f"  Verifying MD5…")
    _verify_md5(dest, md5_url)
    print(f"  MD5 OK — saved: {dest}")
    download_file(md5_url, Path(f"{dest}.md5"))


def download_updates(
    updates_url: str,
    start_seq: int,
    data_dir: Path,
    region_updates_rel: str,
) -> None:
    root_state = fetch_state_file(updates_url)
    if root_state is None:
        raise RuntimeError(f"Could not fetch current state from {updates_url}")
    current_seq = int(root_state["sequenceNumber"])

    updates_dir = data_dir / region_updates_rel
    updates_dir.mkdir(parents=True, exist_ok=True)

    total = current_seq - start_seq
    print(f"  Downloading {total} update sequences ({start_seq} → {current_seq})")

    for seq in range(start_seq + 1, current_seq + 1):
        path_fragment = seq_to_path(seq)
        for ext in (".osc.gz", ".state.txt"):
            url = f"{updates_url}/{path_fragment}{ext}"
            dest = updates_dir / path_fragment.replace("/", "/")
            dest = updates_dir / Path(path_fragment + ext)
            try:
                download_file(url, dest)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    pass  # some sequences may be absent
                else:
                    raise

    # Write root state.txt
    root_state_dest = updates_dir / "state.txt"
    root_state_dest.write_text(
        "\n".join(f"{k}={v}" for k, v in root_state.items()) + "\n"
    )
    print(f"  Updates written to: {updates_dir}")
