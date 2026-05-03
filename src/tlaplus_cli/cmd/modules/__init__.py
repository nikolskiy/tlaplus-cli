import typer

app = typer.Typer(name="modules", help="Manage TLA+ Java modules.", no_args_is_help=True)

from . import build, install, lib, path  # noqa: F401, E402
