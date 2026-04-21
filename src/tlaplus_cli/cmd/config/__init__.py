import typer

app = typer.Typer(name="config", help="Manage application configuration.", no_args_is_help=True)

from . import edit  # noqa: F401, E402
from . import list as list_cmd  # noqa: F401, E402
