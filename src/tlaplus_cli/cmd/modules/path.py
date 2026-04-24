from pathlib import Path

import typer

from tlaplus_cli.cmd.modules import app
from tlaplus_cli.config.loader import load_config, save_config, workspace_root


@app.command(name="path")
def set_modules_path(
    path: str | None = typer.Argument(None, help="Path to the custom Java modules directory, or 'none' to reset."),
) -> None:
    """Configure or view a persistent custom Java modules source path."""
    config_obj = load_config()

    if path is None:
        if config_obj.module_path:
            typer.echo(f"Current modules path: {config_obj.module_path}")
        else:
            default_path = workspace_root() / config_obj.workspace.modules_dir
            typer.echo("Custom modules path is not set.")
            typer.echo(f"Defaulting to: {default_path}")
        return

    if path.lower() == "none":
        config_obj.module_path = None
        save_config(config_obj)
        typer.echo("Custom modules path reset to default.")
        return

    p = Path(path).resolve()

    if not p.is_dir():
        typer.echo(f"Error: Path does not exist or is not a directory: {p}", err=True)
        raise typer.Exit(1)

    config_obj.module_path = str(p)
    save_config(config_obj)
    typer.echo(f"Modules path updated to: {p}")
