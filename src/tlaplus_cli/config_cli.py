"""CLI for managing application configuration."""

import os
import shutil
import subprocess

import typer

from tlaplus_cli.config import _ensure_config, config_path

config_app = typer.Typer(name="config", help="Manage application configuration.", no_args_is_help=True)


@config_app.command(name="list")
def list_config() -> None:
    """Display the current configuration file content."""
    cp = config_path()
    if not cp.exists():
        typer.echo("Configuration file not found.", err=True)
        raise typer.Exit(1)

    with cp.open(encoding="utf-8") as f:
        typer.echo(f.read())


@config_app.command(name="edit")
def edit_config(
    editor: str | None = typer.Argument(None, help="The editor to use (defaults to $EDITOR or 'vim').")
) -> None:
    """Open the configuration file in an editor."""
    cp = config_path()

    # Ensure config exists
    _ensure_config()

    if not editor:

        editor = os.environ.get("EDITOR", "vim")

    editor_path = shutil.which(editor)
    if not editor_path:
        typer.echo(f"Error: Editor '{editor}' not found in PATH.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Opening {cp} with {editor} ...")
    try:
        subprocess.run([editor_path, str(cp)], check=True)
    except subprocess.CalledProcessError as e:
        typer.echo(f"Editor exited with error: {e}", err=True)
        raise typer.Exit(1) from None
