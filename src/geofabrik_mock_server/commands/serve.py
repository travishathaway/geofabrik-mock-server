from pathlib import Path

import click
from werkzeug.serving import make_server

from geofabrik_mock_server.core.server import create_app


@click.command("serve")
@click.option(
    "--port",
    default=8080,
    show_default=True,
    help="Port to listen on. Use 0 to let the OS assign a free port.",
)
@click.option("--host", default="127.0.0.1", show_default=True, help="Host to bind to.")
@click.option(
    "--root-dir",
    envvar="GEOFABRIK_MOCK_SERVER_ROOT_DIR",
    show_default=True,
    help="Root directory to serve from",
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
    server = make_server(host, port, app)
    actual_port = server.socket.getsockname()[1]
    click.echo(f"Geofabrik mock server running at http://{host}:{actual_port}/")
    click.echo("Press Ctrl+C to stop.")
    server.serve_forever()
