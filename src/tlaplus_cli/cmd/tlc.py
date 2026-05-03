import typer

from tlaplus_cli import ui
from tlaplus_cli.config.loader import load_config
from tlaplus_cli.java.classpath import ClasspathResolver
from tlaplus_cli.project import find_project_root
from tlaplus_cli.tlc.compiler import get_tlc_jar_path
from tlaplus_cli.tlc.models import CheckState, CheckStatus, ModelCheckResult
from tlaplus_cli.tlc.runner import (
    build_tlc_command,
    get_tlc_version,
    resolve_spec_file,
    run_tlc,
)


def version_callback(value: bool) -> None:
    if value:
        jar_path = get_tlc_jar_path()
        typer.echo(f"tla2tools.jar path: {jar_path}")

        if not jar_path.exists():
            ui.error(f"tla2tools.jar not found at {jar_path}")
            typer.echo("Run 'tla tools install' first.", err=True)
            raise typer.Exit(1)

        version_str = get_tlc_version()
        if version_str:
            typer.echo(version_str)

        raise typer.Exit(0)


def print_progress(result: ModelCheckResult) -> None:
    """Callback to print progress from ModelCheckResult."""
    if result.status == CheckStatus.SuccessorStatesComputing and result.initial_states_stat:
        last_stat = result.initial_states_stat[-1]
        # Use carriage return to update the same line for progress
        msg = f"Progress: {last_stat.total} states generated, {last_stat.distinct} distinct states found"
        typer.echo(f"\r{msg}", err=True, nl=False)
    elif result.status == CheckStatus.Finished:
        # Final newline after progress
        typer.echo("", err=True)


def _show_diagnostic_info(spec: str, spec_name: str) -> None:
    """Show diagnostic info before running TLC."""
    version_str = get_tlc_version() or "unknown"
    typer.echo(f"Running TLC ({version_str}) on {spec_name} ...")

    # Check if we have TLA-Library
    try:
        config = load_config()
        spec_file, _ = resolve_spec_file(spec)
        project_root = find_project_root(
            spec_file,
            modules_dir=config.workspace.modules_dir,
            classes_dir=config.workspace.classes_dir,
        )
        jar_path = get_tlc_jar_path()
        resolver = ClasspathResolver(config, project_root=project_root, tool_jar=jar_path)
        tla_library = resolver.get_tla_library_property()
        if tla_library:
            ui.info(f"TLA-Library: {tla_library}")
    except Exception:
        pass  # nosec


# PLR0912: This command handler orchestrates multiple output types (errors, warnings, results, progress);
# splitting it would fragment the CLI's primary user-facing logic.
def tlc(  # noqa: PLR0912
    spec: str = typer.Argument(help="Name of the TLA+ specification (without .tla extension)."),
    # Typer requires the parameter in the signature to register the CLI option;
    # since the logic is in the eager callback, the value is not used here.
    version: bool | None = typer.Option(  # noqa: ARG001
        None,
        "--version",
        help="Print the path to tla2tools.jar and its version.",
        callback=version_callback,
        is_eager=True,
    ),
    show_command: bool = typer.Option(False, "--show-command", help="Print the command instead of executing it."),
) -> None:
    """Run TLC model checker on a TLA+ specification."""
    # version argument is handled by version_callback (is_eager=True)
    try:
        _, spec_name = resolve_spec_file(spec)
    except FileNotFoundError as e:
        ui.error(str(e))
        raise typer.Exit(1) from None

    if show_command:
        try:
            cmd = build_tlc_command(spec)
        except FileNotFoundError as e:
            ui.error(str(e))
            raise typer.Exit(1) from None
        typer.echo(" ".join(cmd))
        raise typer.Exit(0)

    _show_diagnostic_info(spec, spec_name)

    try:
        # We need the parser to get the final result, so we'll wrap run_tlc
        # or capture the result from the last callback.
        final_result: list[ModelCheckResult] = []

        def wrapped_callback(res: ModelCheckResult) -> None:
            print_progress(res)
            if not final_result:
                final_result.append(res)
            else:
                final_result[0] = res

        exit_code = run_tlc(spec, callback=wrapped_callback)

        if final_result:
            res = final_result[0]
            if res.state == CheckState.Success:
                ui.success("Model checking completed successfully.")
            elif res.state == CheckState.Error:
                ui.error(f"Model checking failed with {len(res.errors)} error(s).")
                for err in res.errors:
                    for line in err.lines:
                        typer.echo(f"  {line}", err=True)

            if res.warnings:
                ui.warn(f"Found {len(res.warnings)} warning(s).")
                for warn_info in res.warnings:
                    for line in warn_info.lines:
                        typer.echo(f"  {line}", err=True)

            if res.duration:
                ui.info(f"Duration: {res.duration}ms")
    except FileNotFoundError as e:
        ui.error(str(e))
        raise typer.Exit(1) from None

    raise typer.Exit(exit_code)
