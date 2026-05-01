from pathlib import Path

import typer

from tlaplus_cli.cmd.modules import app
from tlaplus_cli.config.loader import load_config, save_config, workspace_root
from tlaplus_cli.java.classpath import ClasspathResolver, ResolveMode, SubdirType
from tlaplus_cli.tlc.compiler import get_tlc_jar_path


@app.command(name="path")
def set_modules_path(
    path: str | None = typer.Argument(None, help="Path to the custom Java modules directory, or 'none' to reset."),
    resolved: bool = typer.Option(False, "--resolved", help="Show the actual resolved paths for the current context."),
) -> None:
    """Configure or view custom Java modules source path."""
    config_obj = load_config()

    if resolved:
        resolver = ClasspathResolver(config_obj, project_root=workspace_root(), tool_jar=get_tlc_jar_path())

        # Source path (modules)
        tla_library = resolver.get_tla_library_property()
        typer.echo(f"Source Path: {tla_library or 'None'}")

        # Classes path
        classes_dir = resolver.get_project_path(SubdirType.CLASSES)
        typer.echo(f"Classes Path: {classes_dir or 'None'}")

        # Library path (JARs)
        libs = resolver.resolve(ResolveMode.RUNTIME)
        # Filter out classes_dir and tool_jar to show only libs
        tool_jar = get_tlc_jar_path()
        only_libs = [p for p in libs if p != str(classes_dir) and p != str(tool_jar)]

        lib_str = "None"
        if only_libs:
            lib_str = f"{len(only_libs)} JARs"

        typer.echo(f"Library Path: {lib_str}")
        if only_libs:
            for lib in only_libs:
                typer.echo(f"  - {lib}")

        # Tool Jar
        typer.echo(f"Tool Jar: {tool_jar}")
        return

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
