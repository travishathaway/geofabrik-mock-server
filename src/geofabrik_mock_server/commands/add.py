import click

from geofabrik_mock_server.core import geofabrik, manifest


@click.command("add")
@click.argument("region_id")
@click.option(
    "--date",
    "start_date",
    metavar="YYYY-MM-DD",
    default=None,
    help="Start date for update diffs (e.g. 2024-01-01). If omitted, only the PBF is downloaded.",
)
def add_command(region_id: str, start_date: str | None) -> None:
    """Add a region to the mock manifest."""
    regions = manifest.load_manifest()

    if manifest.find_region(regions, region_id):
        raise click.ClickException(f"Region '{region_id}' is already in the manifest.")

    click.echo(f"Fetching Geofabrik index to validate '{region_id}'…")
    index = geofabrik.fetch_index()
    feature = geofabrik.find_region_in_index(index, region_id)
    if feature is None:
        raise click.ClickException(
            f"Region '{region_id}' not found in Geofabrik index. "
            "Check https://download.geofabrik.de/index-v1.json for valid IDs."
        )

    props = feature["properties"]
    urls = props.get("urls", {})

    pbf_url = urls.get("pbf")
    updates_url = urls.get("updates")

    if not pbf_url:
        raise click.ClickException(f"No PBF URL found for region '{region_id}'.")

    entry: dict = {
        "id": region_id,
        "name": props.get("name", region_id),
        "pbf_url": pbf_url,
    }
    if updates_url:
        entry["updates_url"] = updates_url
    if start_date:
        entry["start_date"] = start_date

    regions.append(entry)
    manifest.save_manifest(regions)

    click.echo(f"Added '{region_id}' ({entry['name']}) to regions.json.")
    if start_date:
        click.echo(f"  Update diffs will be fetched from {start_date} onwards when you run 'gms download'.")
    if not updates_url:
        click.echo("  Note: no updates URL available for this region.")
