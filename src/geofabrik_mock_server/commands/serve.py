import importlib.resources
from pathlib import Path

import click

from geofabrik_mock_server.core.server import create_app


def _data_root() -> Path:
    ref = importlib.resources.files("geofabrik_mock_server") / "data"
    with importlib.resources.as_file(ref) as p:
        return p


@click.command("serve")
@click.option("--port", default=8080, show_default=True, help="Port to listen on.")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind to.")
@click.option(
    "--root-dir",
    envvar="GEOFABRIK_MOCK_SERVER_ROOT_DIR",
    show_default=True,
    help="Root directory to serve from"
)
def serve_command(port: int, host: str, root_dir: str) -> None:
    """Serve the mock Geofabrik data over HTTP."""
    data_root = Path(root_dir)
    if not any(data_root.iterdir()) if data_root.exists() else True:
        click.echo(
            "Warning: data directory is empty. Run 'gms download' first.",
            err=True,
        )

    app = create_app(data_root)
    click.echo(f"Geofabrik mock server running at http://{host}:{port}/")
    click.echo("Press Ctrl+C to stop.")
    app.run(host=host, port=port)
