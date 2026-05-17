import importlib.resources
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import click

from geofabrik_mock_server.core import geofabrik, manifest

GEOFABRIK_BASE = "https://download.geofabrik.de"


def _data_root() -> Path:
    ref = importlib.resources.files("geofabrik_mock_server") / "data"
    with importlib.resources.as_file(ref) as p:
        return p


def _rel_path_from_url(url: str) -> str:
    """Return the path component of a Geofabrik URL, relative to the base.

    'https://download.geofabrik.de/europe/monaco-latest.osm.pbf'
    → 'europe/monaco-latest.osm.pbf'
    """
    return urlparse(url).path.lstrip("/")


def _build_index_json(regions: list[dict], data_root: Path) -> None:
    """Write a filtered index-v1.json for the mock regions."""
    click.echo("Fetching Geofabrik index to build index-v1.json…")
    full_index = geofabrik.fetch_index()

    features = []
    for region in regions:
        feature = geofabrik.find_region_in_index(full_index, region["id"])
        if feature is None:
            click.echo(f"  Warning: '{region['id']}' not found in live index, skipping.")
            continue
        # Keep only pbf and updates urls
        props = dict(feature.get("properties", {}))
        urls = {k: v for k, v in props.get("urls", {}).items() if k in ("pbf", "updates")}
        props["urls"] = urls
        features.append({**feature, "properties": props})

    index_doc = {
        "type": "FeatureCollection",
        "copyright": "Geofabrik mock — data © OpenStreetMap contributors",
        "features": features,
    }
    dest = data_root / "index-v1.json"
    dest.write_text(json.dumps(index_doc, indent=2) + "\n")
    click.echo(f"  Wrote {dest}")


@click.command("download")
@click.option(
    "--region",
    "region_filter",
    metavar="REGION_ID",
    default=None,
    help="Download only this region (default: all regions in manifest).",
)
def download_command(region_filter: str | None) -> None:
    """Download PBF and update diffs for all manifest regions."""
    regions = manifest.load_manifest()
    if not regions:
        raise click.ClickException(
            "No regions in manifest. Run 'gms add <region-id>' first."
        )

    if region_filter:
        regions = [r for r in regions if r["id"] == region_filter]
        if not regions:
            raise click.ClickException(f"Region '{region_filter}' not found in manifest.")

    data_root = _data_root()
    data_root.mkdir(parents=True, exist_ok=True)

    for region in regions:
        region_id = region["id"]
        click.echo(f"\n[{region_id}]")

        pbf_rel = _rel_path_from_url(region["pbf_url"])
        pbf_dest = data_root / pbf_rel
        pbf_dest.parent.mkdir(parents=True, exist_ok=True)

        updates_url = region.get("updates_url")
        start_date_str = region.get("start_date")

        if start_date_str:
            try:
                target = date.fromisoformat(start_date_str)
            except ValueError:
                raise click.ClickException(
                    f"Invalid start_date '{start_date_str}' for region '{region_id}'. "
                    "Expected YYYY-MM-DD."
                )
            # Download the dated snapshot (e.g. monaco-260512.osm.pbf) and save as -latest
            geofabrik.download_pbf_for_date(region["pbf_url"], target, pbf_dest)
        else:
            geofabrik.download_pbf(region["pbf_url"], pbf_dest)

        if updates_url:
            updates_rel = _rel_path_from_url(updates_url)

            if start_date_str:
                click.echo(f"  Resolving sequence number for {start_date_str}…")
                start_seq = geofabrik.resolve_sequence_for_date(updates_url, target)
                click.echo(f"  Start sequence: {start_seq}")
                geofabrik.download_updates(updates_url, start_seq, data_root, updates_rel)
            else:
                # No date specified — just download root state.txt so the endpoint exists
                root_state = geofabrik.fetch_state_file(updates_url)
                if root_state:
                    updates_dir = data_root / updates_rel
                    updates_dir.mkdir(parents=True, exist_ok=True)
                    (updates_dir / "state.txt").write_text(
                        "\n".join(f"{k}={v}" for k, v in root_state.items()) + "\n"
                    )
                    click.echo(f"  Wrote state.txt to {updates_dir}")

    _build_index_json(manifest.load_manifest(), data_root)
    click.echo("\nDownload complete.")
