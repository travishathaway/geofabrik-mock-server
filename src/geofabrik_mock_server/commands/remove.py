import importlib.resources
import shutil
from pathlib import Path

import click

from geofabrik_mock_server.core import manifest


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

    # Determine local data paths to clean up
    data_root = _data_root()
    # region_id is like "europe/andorra" → continent/name
    parts = region_id.split("/")
    if len(parts) == 2:
        continent, name = parts
        candidates = [
            data_root / continent / f"{name}-latest.osm.pbf",
            data_root / continent / f"{name}-updates",
        ]
    else:
        candidates = []

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
