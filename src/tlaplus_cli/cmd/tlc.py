import sys

import typer
from rich.console import Console
from rich.live import Live

from tlaplus_cli import ui
from tlaplus_cli.config.loader import load_config
from tlaplus_cli.java.classpath import ClasspathResolver
from tlaplus_cli.project import find_project_root
from tlaplus_cli.tlc.compiler import get_tlc_jar_path
from tlaplus_cli.tlc.components import StatsTableFormatter, StatusFooterRenderable
from tlaplus_cli.tlc.formatter import TlcFormatter
from tlaplus_cli.tlc.models import CheckState, ModelCheckResult
from tlaplus_cli.tlc.run_cache import clear_tlc_run_cache
from tlaplus_cli.tlc.runner import (
    build_tlc_command,
    get_tlc_version,
    resolve_cfg_file,
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
# PLR0913: CLI command function accepts options as parameters.
# PLR0915: Too many statements.
def tlc(  # noqa: PLR0912, PLR0913, PLR0915
    spec: str | None = typer.Argument(
        None,
        help="Name of the TLA+ specification (without .tla extension).",
    ),
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
    cleanup: bool = typer.Option(False, "--cleanup", help="Purge all cached TLC run artifacts from cache."),
    _refresh_interval: float | None = typer.Option(
        None,
        "--refresh-interval",
        help="Refresh interval for the output (seconds).",
    ),
    coverage: bool = typer.Option(False, "--coverage", help="Enable code coverage visualization."),
    raw: bool = typer.Option(False, "--raw", help="Run TLC in raw mode without structured tool mode formatting."),
    cfg: str | None = typer.Option(
        None,
        "--cfg",
        help="Custom TLC configuration file name or path (e.g. spec-v1 or spec-v1.cfg).",
    ),
) -> None:
    """Run TLC model checker on a TLA+ specification."""
    if cleanup:
        clear_tlc_run_cache()
        ui.success("TLC run cache cleared successfully.")
        raise typer.Exit(0)

    if not spec:
        ui.error("Missing argument 'SPEC'.")
        raise typer.Exit(1)

    # version argument is handled by version_callback (is_eager=True)
    try:
        spec_file, _spec_name = resolve_spec_file(spec)
        if cfg:
            config_obj = load_config()
            project_root = find_project_root(
                spec_file,
                modules_dir=config_obj.workspace.modules_dir,
                classes_dir=config_obj.workspace.classes_dir,
            )
            resolve_cfg_file(cfg, spec_file, project_root=project_root)
    except FileNotFoundError as e:
        ui.error(str(e))
        raise typer.Exit(1) from None

    if show_command:
        cmd = build_tlc_command(spec, cfg=cfg)
        if coverage:
            cmd.extend(["-coverage", "1"])
        if not cmd:
            raise typer.Exit(1) from None
        typer.echo(" ".join(cmd))
        raise typer.Exit(0)

    if raw:
        exit_code = run_tlc(spec, coverage=coverage, raw=True, cfg=cfg)
        raise typer.Exit(exit_code)


    tlc_version = get_tlc_version() or "unknown"
    formatter = TlcFormatter(tlc_version=tlc_version)
    layout = formatter.create_layout()

    is_tty = sys.stdout.isatty()

    try:
        final_result: list[ModelCheckResult] = []
        printed_logs_count = 0
        printed_stats_count = 0
        stats_header_printed = False
        stats_border_printed = False

        if is_tty:
            table_formatter = StatsTableFormatter()
            footer_renderable = StatusFooterRenderable(ModelCheckResult())
            console = Console()

            with Live(footer_renderable, refresh_per_second=4, screen=False) as live:

                def wrapped_callback(res: ModelCheckResult) -> None:
                    nonlocal printed_logs_count, printed_stats_count, stats_header_printed, stats_border_printed

                    # Keep tests happy by updating the formatter
                    formatter.update(layout, res)

                    if not final_result:
                        final_result.append(res)
                    else:
                        final_result[0] = res

                    # Update the live status footer dynamic data
                    footer_renderable.result = res

                    # Stream any new logs
                    if len(res.output_lines) > printed_logs_count:
                        new_logs = res.output_lines[printed_logs_count:]
                        for log in new_logs:
                            live.console.print(log.strip())
                        printed_logs_count = len(res.output_lines)

                    # Stream any new progress stats
                    if len(res.initial_states_stat) > printed_stats_count:
                        new_stats = res.initial_states_stat[printed_stats_count:]
                        for stat in new_stats:
                            if not stats_header_printed:
                                live.console.print("\nState Space Progress:\n")
                                live.console.print(table_formatter.get_header())
                                live.console.print(table_formatter.get_border())
                                stats_header_printed = True

                            row_str = table_formatter.format_row(stat)
                            live.console.print(row_str)
                        printed_stats_count = len(res.initial_states_stat)

                    # Print bottom border when execution changes state to non-running
                    if res.state != CheckState.Running and stats_header_printed and not stats_border_printed:
                        live.console.print(table_formatter.get_border())
                        stats_border_printed = True

                exit_code = run_tlc(spec, callback=wrapped_callback, coverage=coverage, cfg=cfg)
        else:
            # Non-TTY mode: no Live block
            table_formatter = StatsTableFormatter()
            print(f"Starting TLC model checker (version {tlc_version}).")

            def wrapped_callback(res: ModelCheckResult) -> None:
                nonlocal printed_logs_count, printed_stats_count, stats_header_printed, stats_border_printed

                # Keep tests happy by updating the formatter
                formatter.update(layout, res)

                if not final_result:
                    final_result.append(res)
                else:
                    final_result[0] = res

                # Stream any new logs
                if len(res.output_lines) > printed_logs_count:
                    new_logs = res.output_lines[printed_logs_count:]
                    for log in new_logs:
                        print(log.strip())
                    printed_logs_count = len(res.output_lines)

                # Stream any new progress stats
                if len(res.initial_states_stat) > printed_stats_count:
                    new_stats = res.initial_states_stat[printed_stats_count:]
                    for stat in new_stats:
                        if not stats_header_printed:
                            print("\nState Space Progress:\n")
                            print(table_formatter.get_header())
                            print(table_formatter.get_border())
                            stats_header_printed = True

                        row_str = table_formatter.format_row(stat)
                        print(row_str)
                    printed_stats_count = len(res.initial_states_stat)

                # Print bottom border when execution changes state to non-running
                if res.state != CheckState.Running and stats_header_printed and not stats_border_printed:
                    print(table_formatter.get_border())
                    stats_border_printed = True

            exit_code = run_tlc(spec, callback=wrapped_callback, coverage=coverage, cfg=cfg)

        # Fallback print of border if not printed yet
        if stats_header_printed and not stats_border_printed:
            if is_tty:
                console.print(table_formatter.get_border())
            else:
                print(table_formatter.get_border())
            stats_border_printed = True

        if final_result:
            res = final_result[0]

            if res.sany_errors:
                console = Console()
                spec_file, _ = resolve_spec_file(spec)
                for sany_err in res.sany_errors:
                    console.print(formatter.render_sany_error(sany_err, spec_file))

            if res.state == CheckState.Success:
                ui.success("Model checking completed successfully.")
            elif res.state == CheckState.Error:
                ui.error(f"Model checking failed with {len(res.errors)} error(s).")
                for err in res.errors:
                    if err.error_trace:
                        console = Console()
                        console.print(formatter.render_error_trace(err.error_trace))
                    else:
                        for line in err.lines:
                            typer.echo(f"  {line}", err=True)

            if res.warnings:
                ui.warn(f"Found {len(res.warnings)} warning(s).")
                for warn_info in res.warnings:
                    for line in warn_info.lines:
                        typer.echo(f"  {line}", err=True)

            if res.coverage_stat:
                console = Console()
                console.print(formatter.render_coverage_table(res.coverage_stat))

                # Show inline coverage for the main spec
                spec_file, _ = resolve_spec_file(spec)
                console.print(formatter.render_inline_coverage(res.coverage_stat, spec_file))

            if res.duration:
                ui.info(f"Duration: {res.duration}ms")
    except FileNotFoundError as e:
        ui.error(str(e))
        raise typer.Exit(1) from None

    raise typer.Exit(exit_code)
