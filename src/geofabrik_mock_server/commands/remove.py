import importlib.resources
import shutil
from pathlib import Path
from urllib.parse import urlparse

import click

from geofabrik_mock_server.core import manifest


def _rel_path_from_url(url: str) -> str:
    return urlparse(url).path.lstrip("/")


def _data_root() -> Path:
    ref = importlib.resources.files("geofabrik_mock_server") / "data"
    with importlib.resources.as_file(ref) as p:
        return p


@click.command("remove")
@click.argument("region_id")
@click.option("--yes", "-y", is_flag=True, help="Delete local data without prompting.")
def remove_command(region_id: str, yes: bool) -> None:
    """Remove a region from the mock manifest."""
    regions = manifest.load_manifest()
    region = manifest.find_region(regions, region_id)

    if region is None:
        raise click.ClickException(f"Region '{region_id}' is not in the manifest.")

    regions = [r for r in regions if r["id"] != region_id]
    manifest.save_manifest(regions)
    click.echo(f"Removed '{region_id}' from regions.json.")

    # Determine local data paths to clean up using stored URLs (not region_id string)
    data_root = _data_root()
    candidates = []
    if region.get("pbf_url"):
        candidates.append(data_root / _rel_path_from_url(region["pbf_url"]))
    if region.get("updates_url"):
        candidates.append(data_root / _rel_path_from_url(region["updates_url"]))

    existing = [p for p in candidates if p.exists()]
    if not existing:
        return

    if not yes:
        click.echo("Local data files found:")
        for p in existing:
            click.echo(f"  {p}")
        yes = click.confirm("Delete them?", default=False)

    if yes:
        for p in existing:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            click.echo(f"  Deleted: {p}")
