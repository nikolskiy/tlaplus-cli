import typer

from tlaplus_cli.cmd.tools.meta import app as meta_app

app = typer.Typer(name="tools", help="Manage TLC tools (tla2tools.jar).", no_args_is_help=True)
app.add_typer(meta_app, name="meta")

from . import dir, install, list, path, pin, uninstall, upgrade  # noqa: F401, E402
