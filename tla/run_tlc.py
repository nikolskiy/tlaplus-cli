"""Run TLC model checker on a TLA+ specification."""

import os
import subprocess

import typer

from tla.check_java import check_java_version
from tla.config import cache_dir, load_config, workspace_root


def tlc(
    spec: str = typer.Argument(help="Name of the TLA+ specification (without .tla extension)."),
) -> None:
    """Run TLC model checker on a TLA+ specification."""
    config = load_config()

    # Check Java version before proceeding
    check_java_version(config.java.min_version)

    # Jar lives in the cache directory
    jar_path = cache_dir() / config.tla.jar_name
    if not jar_path.exists():
        typer.echo(f"Error: {config.tla.jar_name} not found at {jar_path}", err=True)
        typer.echo("Run 'tla download tla' first.", err=True)
        raise typer.Exit(1)

    ws_root = workspace_root()
    spec_dir = ws_root / config.workspace.spec_dir
    spec_file = spec_dir / f"{spec}.tla"
    if not spec_file.exists():
        typer.echo(f"Error: specification not found: {spec_file}", err=True)
        raise typer.Exit(1)

    classpath = str(jar_path)
    classes_path = ws_root / config.workspace.classes_dir
    if classes_path.exists():
        classpath = f"{classes_path}{os.pathsep}{classpath}"

    cmd = ["java", *config.java.opts, "-cp", classpath, config.tlc.java_class, str(spec_file)]

    typer.echo(f"Running TLC on {spec}.tla ...")
    typer.echo(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(spec_dir))
    raise typer.Exit(result.returncode)
