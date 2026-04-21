import subprocess
from pathlib import Path

import typer

from tlaplus_cli.cmd.modules import app
from tlaplus_cli.tlc.compiler import compile_modules


@app.command(name="build")
def build(
    path: str | None = typer.Argument(None, help="Project root directory (defaults to workspace root)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show compilation output."),
) -> None:
    """Compile custom Java modules."""
    base_dir = Path(path).resolve() if path is not None else None

    typer.echo("Compiling Java files ...")
    try:
        classes_dir = compile_modules(base_dir, verbose)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except subprocess.CalledProcessError:
        typer.echo("Compilation failed!", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Successfully compiled to {classes_dir}")
    service_file = classes_dir / "META-INF" / "services" / "tlc2.overrides.ITLCOverrides"
    typer.echo(f"Created service file at {service_file}")
