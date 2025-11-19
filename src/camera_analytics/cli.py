"""Command-line interface for camera analytics."""

import logging

import click

from camera_analytics.config import get_settings
from camera_analytics.utils.logging import setup_logging

settings = get_settings()
logger = logging.getLogger(__name__)


@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging")
def main(debug: bool):
    """Camera Analytics CLI."""
    setup_logging(level="DEBUG" if debug else settings.log_level)


@main.command()
def version():
    """Show version information."""
    from camera_analytics import __version__

    click.echo(f"Camera Analytics v{__version__}")


@main.group()
def camera():
    """Camera management commands."""
    pass


@camera.command("list")
def camera_list():
    """List all cameras."""
    click.echo("No cameras configured")


@main.group()
def db():
    """Database management commands."""
    pass


@db.command("migrate")
def db_migrate():
    """Run database migrations."""
    click.echo("Running database migrations...")


if __name__ == "__main__":
    main()
