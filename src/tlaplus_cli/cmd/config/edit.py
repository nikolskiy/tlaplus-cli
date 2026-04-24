import os
import shutil
import subprocess

import typer

from tlaplus_cli.cmd.config import app
from tlaplus_cli.config.loader import config_path, load_config


@app.command(name="edit")
def edit_config(
    editor: str | None = typer.Argument(None, help="The editor to use (defaults to $EDITOR or 'vim')."),
) -> None:
    """Open the configuration file in an editor."""
    cp = config_path()

    # Ensure config exists by loading it
    load_config()

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
