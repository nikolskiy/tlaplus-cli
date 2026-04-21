import typer

app = typer.Typer(name="meta", help="Manage metadata for installed tools.", no_args_is_help=True)

from . import sync  # noqa: F401, E402
