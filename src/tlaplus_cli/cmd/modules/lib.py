from pathlib import Path

import typer

from tlaplus_cli.cmd.modules import app
from tlaplus_cli.config.loader import load_config, save_config, workspace_root


@app.command(name="lib")
def set_modules_lib_path(
    path: str | None = typer.Argument(
        None, help="Path to the custom Java modules dependencies directory, or 'none' to reset."
    )
) -> None:
    """Configure or view a persistent custom Java modules dependencies (lib) path."""
    config_obj = load_config()

    if path is None:
        if config_obj.module_lib_path:
            typer.echo(f"Current modules lib path: {config_obj.module_lib_path}")
        else:
            modules_dir = (
                Path(config_obj.module_path)
                if config_obj.module_path
                else workspace_root() / config_obj.workspace.modules_dir
            )
            default_path = modules_dir / "lib"
            typer.echo("Custom modules lib path is not set.")
            typer.echo(f"Defaulting to: {default_path}")
        return

    if path.lower() == "none":
        config_obj.module_lib_path = None
        save_config(config_obj)
        typer.echo("Custom modules lib path reset to default.")
        return

    p = Path(path).resolve()

    if not p.is_dir():
        typer.echo(f"Error: Path does not exist or is not a directory: {p}", err=True)
        raise typer.Exit(1)

    config_obj.module_lib_path = str(p)
    save_config(config_obj)
    typer.echo(f"Modules lib path updated to: {p}")
