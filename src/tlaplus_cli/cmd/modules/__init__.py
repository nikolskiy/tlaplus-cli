import typer

app = typer.Typer(name="modules", help="Manage TLA+ Java modules.", no_args_is_help=True)


# Import functions for new commands
from .add import add_module  # noqa: E402
from .list import list_modules  # noqa: E402
from .path import show_modules_path  # noqa: E402
from .remove import remove_module  # noqa: E402

# Register new commands with the typer app
app.command(name="add")(add_module)
app.command(name="list")(list_modules)
app.command(name="remove")(remove_module)
app.command(name="path")(show_modules_path)
