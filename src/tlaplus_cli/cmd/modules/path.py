import os
from pathlib import Path

import typer

from tlaplus_cli.config.loader import load_config
from tlaplus_cli.java.classpath import ClasspathResolver, ResolveMode, SubdirType
from tlaplus_cli.tlc.compiler import get_tlc_jar_path
from tlaplus_cli.versioning.paths import get_modules_dir


def show_modules_path() -> None:  # noqa: PLR0912
    """Display the active paths that will be included when running TLC."""
    config_obj = load_config()
    tool_jar = get_tlc_jar_path()

    resolver = ClasspathResolver(config_obj, project_root=None, tool_jar=tool_jar)

    # 1. Source Paths (-DTLA-Library)
    tla_library = resolver.get_tla_library_property()
    typer.echo("Source Paths (-DTLA-Library):")
    if tla_library:
        for p in tla_library.split(os.pathsep):
            typer.echo(f"  - {p}")
    else:
        typer.echo("  None")

    # 2. Classes Paths
    classes_paths = []
    project_classes = resolver.get_project_path(SubdirType.CLASSES)
    if project_classes:
        classes_paths.append(str(project_classes.absolute()))

    managed_dir = get_modules_dir()
    if managed_dir.is_dir():
        for item in sorted(managed_dir.iterdir()):
            if item.is_dir():
                mod_classes = item / "classes"
                if mod_classes.is_dir():
                    classes_paths.append(str(mod_classes.absolute()))

    typer.echo("\nClasses Paths:")
    if classes_paths:
        for p in classes_paths:
            typer.echo(f"  - {p}")
    else:
        typer.echo("  None")

    # 3. Library Paths (JARs)
    libs = resolver.resolve(ResolveMode.RUNTIME)
    tool_jar_abs = str(tool_jar.absolute()) if tool_jar.exists() else ""

    # Filter out classes directories and tool_jar to show only external library JARs
    only_libs = []
    for p in libs:
        if p == tool_jar_abs:
            continue
        p_path = Path(p)
        if p_path.name == "classes" and p_path.is_dir():
            continue
        only_libs.append(p)

    typer.echo("\nLibrary Paths (JARs):")
    if only_libs:
        for p in only_libs:
            typer.echo(f"  - {p}")
    else:
        typer.echo("  None")
