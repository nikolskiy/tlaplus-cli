"""Compile custom TLC modules (Java)."""

import os
import subprocess
from pathlib import Path

import typer

from tlaplus_cli.config import cache_dir, load_config, save_config, workspace_root
from tlaplus_cli.version_manager import get_pinned_version_dir


def build(
    path: str | None = typer.Argument(None, help="Project root directory (defaults to workspace root)."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show compilation output."),
) -> None:
    """Compile custom Java modules."""
    config = load_config()
    base_dir = Path(path).resolve() if path is not None else workspace_root()

    # Fallback chain: pinned directory -> legacy jar
    pinned_dir = get_pinned_version_dir()
    pinned_jar = pinned_dir / "tla2tools.jar" if pinned_dir else None
    legacy = cache_dir() / "tla2tools.jar"
    jar_path = pinned_jar if (pinned_jar and pinned_jar.exists()) else legacy

    if not jar_path.exists():
        typer.echo("Error: tla2tools.jar not found.\nRun 'tla tools install' first.", err=True)
        raise typer.Exit(1)

    modules_dir = Path(config.module_path) if config.module_path else base_dir / config.workspace.modules_dir
    classes_dir = base_dir / config.workspace.classes_dir

    lib_dir = Path(config.module_lib_path) if config.module_lib_path else modules_dir / "lib"

    lib_jars = sorted(lib_dir.glob("*.jar")) if lib_dir.is_dir() else []
    classpath = os.pathsep.join([str(jar_path)] + [str(j) for j in lib_jars])

    if not modules_dir.exists():
        typer.echo(f"Error: modules directory not found: {modules_dir}", err=True)
        raise typer.Exit(1)

    java_files = list(modules_dir.rglob("*.java"))
    if not java_files:
        typer.echo(f"No Java source files found in {modules_dir}", err=True)
        return

    typer.echo(f"Compiling {len(java_files)} Java files from {modules_dir} ...")
    classes_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["javac", "-cp", classpath, "-d", str(classes_dir), *[str(f) for f in java_files]]

    try:
        result = subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
        typer.echo(f"Successfully compiled to {classes_dir}")
        if verbose and result.stdout:
            typer.echo(result.stdout)

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


def set_modules_path(
    path: str | None = typer.Argument(None, help="Path to the custom Java modules directory, or 'none' to reset.")
) -> None:
    """Configure or view a persistent custom Java modules path."""
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
