import sys
from importlib.metadata import version

import click

from geofabrik_mock_server.commands.add import add_command
from geofabrik_mock_server.commands.download import download_command
from geofabrik_mock_server.commands.remove import remove_command
from geofabrik_mock_server.commands.serve import serve_command


@click.group()
@click.version_option(version("geofabrik-mock-server"), "-v", "--version")
def cli() -> None:
    """Geofabrik Mock Server — serve a local mock of download.geofabrik.de."""


cli.add_command(add_command)
cli.add_command(remove_command)
cli.add_command(download_command)
cli.add_command(serve_command)


def main() -> None:
    cli()


if __name__ == "__main__":
    sys.exit(main())
