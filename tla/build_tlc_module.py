"""Compile custom TLC modules (Java)."""

import subprocess

import typer

from tla.config import cache_dir, load_config, workspace_root


def build(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show compilation output."),
) -> None:
    """Compile custom Java modules."""
    config = load_config()

    # Jar lives in the cache directory
    jar_path = cache_dir() / config.tla.jar_name

    ws_root = workspace_root()
    modules_dir = ws_root / config.workspace.modules_dir
    classes_dir = ws_root / config.workspace.classes_dir

    if not jar_path.exists():
        typer.echo(f"Error: {config.tla.jar_name} not found at {jar_path}", err=True)
        typer.echo("Run 'tla download tla' first.", err=True)
        raise typer.Exit(1)

    if not modules_dir.exists():
        typer.echo(f"Error: modules directory not found: {modules_dir}", err=True)
        raise typer.Exit(1)

    # Find all .java files in modules dir
    java_files = list(modules_dir.rglob("*.java"))
    if not java_files:
        typer.echo(f"No Java source files found in {modules_dir}", err=True)
        return

    typer.echo(f"Compiling {len(java_files)} Java files from {modules_dir} ...")

    # Ensure output dir exists
    classes_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["javac", "-cp", str(jar_path), "-d", str(classes_dir), *[str(f) for f in java_files]]

    try:
        result = subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
        typer.echo(f"Successfully compiled to {classes_dir}")
        if verbose and result.stdout:
            typer.echo(result.stdout)

        # Create META-INF/services/tlc2.overrides.ITLCOverrides
        meta_inf = classes_dir / "META-INF" / "services"
        meta_inf.mkdir(parents=True, exist_ok=True)
        service_file = meta_inf / "tlc2.overrides.ITLCOverrides"

        with service_file.open("w") as f:
            f.write(f"{config.tlc.overrides_class}\n")

        typer.echo(f"Created service file at {service_file}")

    except subprocess.CalledProcessError as e:
        typer.echo("Compilation failed!", err=True)
        if e.stdout:
            typer.echo(e.stdout, err=True)
        if e.stderr:
            typer.echo(e.stderr, err=True)
        raise typer.Exit(1) from None
    except FileNotFoundError:
        typer.echo("Error: 'javac' not found. Ensure JDK is installed and in PATH.", err=True)
        raise typer.Exit(1) from None
