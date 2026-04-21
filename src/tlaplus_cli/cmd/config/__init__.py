import typer

app = typer.Typer(name="config", help="Manage application configuration.", no_args_is_help=True)

from . import edit, list  # noqa: F401, E402
