import typer

from tlaplus_cli.tlc.compiler import get_tlc_jar_path
from tlaplus_cli.tlc.runner import get_tlc_version, resolve_spec_file, run_tlc


def version_callback(value: bool) -> None:
    if value:
        jar_path = get_tlc_jar_path()
        typer.echo(f"tla2tools.jar path: {jar_path}")

        if not jar_path.exists():
            typer.echo(f"Error: tla2tools.jar not found at {jar_path}", err=True)
            typer.echo("Run 'tla tools install' first.", err=True)
            raise typer.Exit(1)

        version_str = get_tlc_version()
        if version_str:
            typer.echo(version_str)

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

    try:
        _, spec_name = resolve_spec_file(spec)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"Running TLC on {spec_name} ...")
    try:
        exit_code = run_tlc(spec)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    raise typer.Exit(exit_code)
