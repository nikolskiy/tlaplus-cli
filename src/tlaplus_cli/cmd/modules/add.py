import datetime
import json
import os
import shutil
import subprocess
from pathlib import Path

import typer

from tlaplus_cli.config.loader import load_config
from tlaplus_cli.java.classpath import ClasspathResolver, ResolveMode
from tlaplus_cli.tlc.compiler import get_tlc_jar_path
from tlaplus_cli.versioning.paths import get_modules_dir


def add_module(  # noqa: PLR0915
    path: str = typer.Argument(..., help="Path to the module directory to add."),
) -> None:
    """Compile custom Java overrides and add/update the module in the cache."""
    source_dir = Path(path).resolve()
    if not source_dir.is_dir():
        typer.echo(f"Error: Path does not exist or is not a directory: {source_dir}", err=True)
        raise typer.Exit(1)

    config = load_config()
    module_name = source_dir.name
    target_dir = get_modules_dir() / module_name

    # Overwrite if exists
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy directories (lib, modules, tlc2, and test/tests)
    def copy_subfolder(subname: str) -> None:
        src = source_dir / subname
        if src.is_dir():
            shutil.copytree(src, target_dir / subname)

    typer.echo("Copying subfolders (lib, modules, test, tlc2)...")
    copy_subfolder("lib")
    copy_subfolder("modules")
    copy_subfolder("tlc2")

    if (source_dir / "test").is_dir():
        copy_subfolder("test")
    elif (source_dir / "tests").is_dir():
        copy_subfolder("tests")

    # 2. Compile Java overrides in cached version if tlc2/overrides exists
    java_files = []
    for candidate in [target_dir / "modules" / "tlc2" / "overrides", target_dir / "tlc2" / "overrides"]:
        if candidate.is_dir():
            java_files.extend(list(candidate.rglob("*.java")))

    if java_files:
        # Build classpath including tool_jar and local libs from the cached folder
        cached_lib = target_dir / "lib"
        extra_libs = []
        if cached_lib.is_dir():
            extra_libs.extend([str(j.absolute()) for j in cached_lib.glob("*.jar")])

        tool_jar = get_tlc_jar_path()
        if not tool_jar.exists():
            typer.echo("Error: tla2tools.jar not found. Run 'tla tools install' first.", err=True)
            shutil.rmtree(target_dir, ignore_errors=True)
            raise typer.Exit(1)

        resolver = ClasspathResolver(config, project_root=None, tool_jar=tool_jar, extra_libs=extra_libs)
        classpath = os.pathsep.join(resolver.resolve(ResolveMode.COMPILE))

        classes_dir = target_dir / "classes"
        classes_dir.mkdir(parents=True, exist_ok=True)

        cmd = ["javac", "-cp", classpath, "-d", str(classes_dir), *[str(f) for f in java_files]]
        typer.echo("Compiling Java files in cached tlc2/overrides...")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except FileNotFoundError as err:
            typer.echo("Error: 'javac' not found. Ensure JDK is installed.", err=True)
            shutil.rmtree(target_dir, ignore_errors=True)
            raise typer.Exit(1) from err
        except subprocess.CalledProcessError as err:
            typer.echo("Compilation failed!", err=True)
            typer.echo(err.stdout, err=True)
            typer.echo(err.stderr, err=True)
            shutil.rmtree(target_dir, ignore_errors=True)
            raise typer.Exit(1) from err

        # Write service file
        meta_inf = classes_dir / "META-INF" / "services"
        meta_inf.mkdir(parents=True, exist_ok=True)
        service_file = meta_inf / "tlc2.overrides.ITLCOverrides"
        with service_file.open("w") as f:
            f.write(f"{config.tlc.overrides_class}\n")

    # 3. Create metadata.json
    metadata = {"name": module_name, "built_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    with (target_dir / "metadata.json").open("w") as f:
        json.dump(metadata, f, indent=2)

    typer.echo(f"Module '{module_name}' successfully added to cache.")
