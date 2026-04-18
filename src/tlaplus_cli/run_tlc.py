"""Run TLC model checker on a TLA+ specification."""

import os
import subprocess
from pathlib import Path

import typer

from tlaplus_cli.check_java import check_java_version
from tlaplus_cli.config import cache_dir, load_config
from tlaplus_cli.project import find_project_root
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
        typer.echo("Error: tla2tools.jar not found.\nRun 'tla tools install' first.", err=True)
        raise typer.Exit(1)

    # Spec resolution logic
    spec_path = Path(spec)
    candidates = [spec_path, spec_path.with_suffix(".tla"), spec_path.parent / "spec" / (spec_path.name + ".tla")]

    spec_file = next((c for c in candidates if c.is_file()), None)
    if not spec_file:
        typer.echo("Error: Could not find a TLA+ spec file. Looked in the following locations:", err=True)
        for c in candidates:
            typer.echo(f"- {c}", err=True)
        raise typer.Exit(1)

    spec_file = spec_file.absolute()
    project_root = find_project_root(
        spec_file, modules_dir=config.workspace.modules_dir, classes_dir=config.workspace.classes_dir
    )

    classpath_parts = [str(jar_path)]
    extra_jvm_opts: list[str] = []

    if config.module_path:
        custom_path = Path(config.module_path)
        if custom_path.is_dir():
            # Phase 4: safely append the custom directory path to the Java -cp mechanism
            classpath_parts.append(str(custom_path))
            # Also add to TLA-Library for convenience if TLA modules are there
            extra_jvm_opts.append(f"-DTLA-Library={custom_path}")

    if project_root:
        classes_path = project_root / config.workspace.classes_dir
        if classes_path.is_dir():
            classpath_parts.insert(0, str(classes_path))
        lib_dir = project_root / "lib"
        if lib_dir.is_dir():
            classpath_parts.extend(str(j) for j in sorted(lib_dir.glob("*.jar")))
        modules_path = project_root / config.workspace.modules_dir
        if modules_path.is_dir():
            extra_jvm_opts.append(f"-DTLA-Library={modules_path}")

    cmd = [
        "java",
        *config.java.opts,
        *extra_jvm_opts,
        "-cp",
        os.pathsep.join(classpath_parts),
        config.tlc.java_class,
        spec_file.name,
    ]

    typer.echo(f"Running TLC on {spec_file.name} ...\nCommand: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(spec_file.parent))
    raise typer.Exit(result.returncode)
