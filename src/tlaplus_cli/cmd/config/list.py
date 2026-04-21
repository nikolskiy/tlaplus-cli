import typer

from tlaplus_cli.cmd.config import app
from tlaplus_cli.config.loader import config_path


@app.command(name="list")
def list_config() -> None:
    """Display the current configuration file content."""
    cp = config_path()
    if not cp.exists():
        typer.echo("Configuration file not found.", err=True)
        raise typer.Exit(1)

    with cp.open(encoding="utf-8") as f:
        typer.echo(f.read())
