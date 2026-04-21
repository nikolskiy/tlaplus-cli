import typer

from tlaplus_cli.cmd.fetch_cache import app
from tlaplus_cli.versioning import clear_cache


@app.command(name="clear")
def cmd_clear_cache() -> None:
    """Clear the local cache of remote GitHub versions."""
    clear_cache()
    typer.echo("GitHub versions cache cleared.")
