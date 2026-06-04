import shutil

import typer

from tlaplus_cli.versioning.paths import get_modules_dir


def remove_module(module_name: str = typer.Argument(..., help="Name of the module to remove from cache.")) -> None:
    """Remove a custom module from the cache."""
    target_dir = get_modules_dir() / module_name
    if not target_dir.is_dir():
        typer.echo(f"Error: Module '{module_name}' not found in cache.", err=True)
        raise typer.Exit(1)

    try:
        shutil.rmtree(target_dir)
        typer.echo(f"Module '{module_name}' successfully deleted from cache.")
    except OSError as e:
        typer.echo(f"Error: Failed to delete module: {e}", err=True)
        raise typer.Exit(1) from e
