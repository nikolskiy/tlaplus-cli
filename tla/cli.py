"""TLA+ CLI tool - entry point."""

import importlib.metadata

import typer

from tla.build_tlc_module import build as build_tlc_cmd
from tla.check_java import check_java_version, get_java_version
from tla.config import load_config
from tla.download_tla2tools import tla as download_tla_cmd
from tla.run_tlc import tlc as run_tlc_cmd

app = typer.Typer(
    name="tla",
    help="TLA+ tools: download TLC, compile custom modules, run model checker.",
    no_args_is_help=True,
    add_completion=False,
)


def version_callback(value: bool) -> None:
    if value:
        meta = importlib.metadata.metadata("tla-cli")
        typer.echo(f"{meta['Name']} v{meta['Version']}")
        typer.echo(meta["Summary"])
        raise typer.Exit()


@app.callback()
def root(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """TLA+ CLI tool."""
    # Load config early to trigger first-run copy
    load_config()
    if version:
        # This branch is effectively redundant due to callback, but keeps type checker happy
        pass


# --- Subcommands ---

# Register 'download' directly as a command, effectively 'tla download'
app.command(name="download")(download_tla_cmd)

app.command(name="tlc")(run_tlc_cmd)
app.command(name="build")(build_tlc_cmd)


@app.command(name="check-java")
def check_java() -> None:
    """Check if Java is installed and meets the minimum version requirement."""
    config = load_config()
    version = get_java_version()
    if version:
        typer.echo(f"Detected Java version: {version}")
    check_java_version(config.java.min_version)
    typer.echo(f"Java version is compatible (>= {config.java.min_version}).")


def main() -> None:
    """Entry point for [project.scripts]."""
    app()
