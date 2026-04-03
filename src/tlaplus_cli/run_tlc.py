"""Run TLC model checker on a TLA+ specification."""

import os
import subprocess
from pathlib import Path

import typer

from tlaplus_cli.check_java import check_java_version
from tlaplus_cli.config import cache_dir, load_config, workspace_root
from tlaplus_cli.version_manager import get_pinned_version_dir


def version_callback(value: bool) -> None:
    if value:
        config = load_config()
        pinned_dir = get_pinned_version_dir()
        pinned_jar = pinned_dir / "tla2tools.jar" if pinned_dir else None
        legacy = cache_dir() / "tla2tools.jar"
        jar_path = pinned_jar if (pinned_jar and pinned_jar.exists()) else legacy
        typer.echo(f"tla2tools.jar path: {jar_path}")

        if not jar_path.exists():
            typer.echo(f"Error: tla2tools.jar not found at {jar_path}", err=True)
            typer.echo("Run 'tla tools install' first.", err=True)
            raise typer.Exit(1)

        cmd = ["java", "-cp", str(jar_path), config.tlc.java_class]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            output = result.stdout or result.stderr
            if output:
                first_line = output.splitlines()[0]
                typer.echo(first_line)
        except FileNotFoundError as err:
            typer.echo("Error: java not found.", err=True)
            raise typer.Exit(1) from err

        raise typer.Exit(0)


def tlc(
    spec: str = typer.Argument(help="Name of the TLA+ specification (without .tla extension)."),
    version: bool | None = typer.Option(
        None,
        "--version",
        help="Print the path to tla2tools.jar and its version.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Run TLC model checker on a TLA+ specification."""
    if version:
        pass
    config = load_config()

    check_java_version(config.java.min_version)

    # Fallback chain: pinned version → legacy jar
    pinned_dir = get_pinned_version_dir()
    pinned_jar = pinned_dir / "tla2tools.jar" if pinned_dir else None
    legacy = cache_dir() / "tla2tools.jar"
    jar_path = pinned_jar if (pinned_jar and pinned_jar.exists()) else legacy

    if not jar_path.exists():
        typer.echo("Error: tla2tools.jar not found.", err=True)
        typer.echo("Run 'tla tools install' first.", err=True)
        raise typer.Exit(1)

    # Spec resolution logic
    spec_path = Path(spec)

    # Candidate 1: Direct path (handles explicit .tla extension)
    direct_path = spec_path
    # Candidate 2: Missing .tla extension
    missing_extension = spec_path.with_suffix(".tla")
    # Candidate 3: Inside spec/ subdirectory
    inside_spec = spec_path.parent / "spec" / (spec_path.name + ".tla")

    if direct_path.is_file():
        spec_file = direct_path
    elif missing_extension.is_file():
        spec_file = missing_extension
    elif inside_spec.is_file():
        spec_file = inside_spec
    else:
        typer.echo("Error: Could not find a TLA+ spec file. Looked in the following locations:", err=True)
        typer.echo(f"- {direct_path}", err=True)
        typer.echo(f"- {missing_extension}", err=True)
        typer.echo(f"- {inside_spec}", err=True)
        raise typer.Exit(1)

    spec_file = spec_file.absolute()
    spec_dir = spec_file.parent

    classpath = str(jar_path)
    # Check for classes in the workspace root or near the spec?
    # The original code used workspace_root() / config.workspace.classes_dir
    ws_root = workspace_root()

    classes_path = ws_root / config.workspace.classes_dir
    if classes_path.exists():
        classpath = f"{classes_path}{os.pathsep}{classpath}"

    cmd = ["java", *config.java.opts, "-cp", classpath, config.tlc.java_class, spec_file.name]

    typer.echo(f"Running TLC on {spec_file.name} ...")
    typer.echo(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(spec_dir))
    raise typer.Exit(result.returncode)
