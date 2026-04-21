import typer

from tlaplus_cli.cmd.fetch_cache import app
from tlaplus_cli.versioning import clear_cache


@app.command(name="clear")
def cmd_clear_cache() -> None:
    clear_cache()
    typer.echo("GitHub API cache cleared.")
