import typer

app = typer.Typer(name="fetch-cache", help="Manage API fetch cache.", no_args_is_help=True)

from . import clear  # noqa: F401, E402
