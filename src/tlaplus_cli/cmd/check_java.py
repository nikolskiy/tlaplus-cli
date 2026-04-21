import typer

from tlaplus_cli.config.loader import load_config
from tlaplus_cli.java import get_java_version, validate_java_version


def check_java() -> None:
    """Check if Java is installed and meets the minimum version requirement."""
    config = load_config()
    version = get_java_version()
    if version:
        typer.echo(f"Detected Java version: {version}")

    try:
        validate_java_version(config.java.min_version)
        typer.echo(f"Java version is compatible (>= {config.java.min_version}).")
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
