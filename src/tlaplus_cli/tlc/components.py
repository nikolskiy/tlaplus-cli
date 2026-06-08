from datetime import datetime
from typing import Protocol

from rich.align import Align
from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text

from tlaplus_cli.tlc.models import CheckState, InitialStateStatItem, ModelCheckResult


class LogDeduplicator:
    """Groups consecutive identical logs into a single line with a count badge."""

    def __init__(self) -> None:
        self.last_line: str | None = None
        self.count: int = 1

    def process(self, line: str) -> str:
        stripped_line = line.strip()
        if stripped_line == self.last_line:
            self.count += 1
            return f"{stripped_line} ({self.count})"

        self.last_line = stripped_line
        self.count = 1
        return stripped_line


class TlcComponent(Protocol):
    """Protocol for a TLC display component."""

    def render(self, result: ModelCheckResult) -> RenderableType:
        """Render the component based on current model check result."""
        ...


class HeaderComponent:
    """Renders the TLC start header."""

    def __init__(self, tlc_version: str = "unknown") -> None:
        self.tlc_version = tlc_version

    def render(self, _result: ModelCheckResult) -> Text:
        return Text(
            f"Starting TLC model checker (version {self.tlc_version}).",
            style="bold",
        )


class StatusInfoComponent:
    """Renders detailed status info (clock, state, Ctrl+C prompt)."""

    def render(self, result: ModelCheckResult) -> Group:
        status_text = result.status.name
        if result.state == CheckState.Stopped:
            status_text = "canceled"

        if not result.start_date_time:
            elapsed_str = "00:00:00"
            elapsed_style = "dim"
        else:
            if result.state == CheckState.Running:
                elapsed = datetime.now() - result.start_date_time
            else:
                elapsed = (result.end_date_time or datetime.now()) - result.start_date_time
            seconds = int(elapsed.total_seconds())
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            elapsed_style = "bold cyan"

        info_text = Text()
        info_text.append(f"Elapsed time: {elapsed_str}\n", style=elapsed_style)
        info_text.append(f"Status: {status_text}\n")

        if result.state == CheckState.Running:
            info_text.append("Stop with Ctrl + C", style="yellow")

        return Group(Align.center(Text("Status Info", style="bold")), info_text)


class LogsComponent:
    """Renders a window of deduplicated log lines."""

    def __init__(self, limit: int | None = 10) -> None:
        self.limit = limit

    def render(self, result: ModelCheckResult) -> Group:
        deduped_logs: list[str] = []
        temp_dedup = LogDeduplicator()
        for line in result.output_lines:
            processed = temp_dedup.process(line)
            if temp_dedup.count > 1 and deduped_logs:
                deduped_logs[-1] = processed
            else:
                deduped_logs.append(processed)

        log_lines = Text()
        items = deduped_logs
        if self.limit is not None and len(items) > self.limit:
            items = items[-self.limit :]

        for line in items:
            log_lines.append(f"{line}\n")

        return Group(Align.center(Text("TLC instance info", style="bold")), log_lines)


class StatsTableComponent:
    """Renders the State Space Progress table, optionally limited to last N items."""

    def __init__(self, limit: int | None = None) -> None:
        self.limit = limit

    def render(self, result: ModelCheckResult) -> Table:
        table = Table(title="State Space Progress", expand=True)
        table.add_column("Time")
        table.add_column("Diameter", justify="right")
        table.add_column("Found", justify="right")
        table.add_column("Distinct", justify="right")
        table.add_column("Queue", justify="right")

        items = result.initial_states_stat
        if self.limit is not None and len(items) > self.limit:
            items = items[-self.limit :]

        for item in items:
            table.add_row(
                item.timestamp,
                str(item.diameter),
                f"{item.total:,}",
                f"{item.distinct:,}",
                f"{item.queue_size:,}",
            )
        return table


class StatusFooterComponent:
    """Renders a single-line live ticking status bar footer."""

    def render(self, result: ModelCheckResult) -> Text:
        status_text = result.status.name
        if result.state == CheckState.Stopped:
            status_text = "canceled"
        elif result.state == CheckState.Success:
            status_text = "success"
        elif result.state == CheckState.Error:
            status_text = "failed"

        if not result.start_date_time:
            elapsed_str = "00:00:00"
            elapsed_style = "dim"
        else:
            if result.state == CheckState.Running:
                elapsed = datetime.now() - result.start_date_time
            else:
                elapsed = (result.end_date_time or datetime.now()) - result.start_date_time
            seconds = int(elapsed.total_seconds())
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            elapsed_style = "bold cyan"

        latest_stats = ""
        if result.initial_states_stat:
            latest = result.initial_states_stat[-1]
            latest_stats = (
                f" | Diam: {latest.diameter} | Gen: {latest.total:,} | "
                f"Dist: {latest.distinct:,} | Queue: {latest.queue_size:,}"
            )

        footer = Text()
        footer.append("TLC Status: ", style="bold")
        footer.append(status_text, style="cyan")
        footer.append(f" | Elapsed: {elapsed_str}", style=elapsed_style)
        if latest_stats:
            footer.append(latest_stats)

        if result.state == CheckState.Running:
            footer.append(" | Stop with Ctrl + C", style="yellow dim")

        return footer


class TlcDisplayComposer:
    """Composes and arranges multiple components."""

    def __init__(self) -> None:
        self.components: dict[str, TlcComponent] = {}

    def register(self, name: str, component: TlcComponent) -> None:
        self.components[name] = component

    def get(self, name: str) -> TlcComponent:
        return self.components[name]

    def render(self, name: str, result: ModelCheckResult) -> RenderableType:
        return self.components[name].render(result)


class StatsTableFormatter:
    """Formats sequential progress table output with 14-char value columns."""

    def __init__(self, value_col_width: int = 14) -> None:
        self.w = value_col_width

    def get_header(self) -> str:
        h_diam = "Diameter".center(10)
        h_found = "Found".center(self.w)
        h_distinct = "Distinct".center(self.w)
        h_queue = "Queue".center(self.w)
        h_date = "Date".center(10)
        h_time = "Time".center(10)
        return f" {h_diam} {h_found} {h_distinct} {h_queue}  {h_date} {h_time} "

    def get_border(self) -> str:
        b_diam = "─" * 10
        b_found = "─" * self.w
        b_distinct = "─" * self.w
        b_queue = "─" * self.w
        b_date = "─" * 10
        b_time = "─" * 10
        return f" {b_diam} {b_found} {b_distinct} {b_queue}  {b_date} {b_time} "

    def format_row(self, item: InitialStateStatItem) -> str:
        parts = item.timestamp.split(" ")
        date_str = parts[0] if len(parts) > 0 else ""
        time_str = parts[1] if len(parts) > 1 else ""

        found_str = f"{item.total:,}"
        distinct_str = f"{item.distinct:,}"
        queue_str = f"{item.queue_size:,}"

        return (
            f" {item.diameter!s:>10} "
            f"{found_str:>{self.w}} "
            f"{distinct_str:>{self.w}} "
            f"{queue_str:>{self.w}}  "
            f"{date_str:<10} "
            f"{time_str:<10} "
        )


class StatusFooterRenderable:
    """Renders a 3-line live ticking status bar footer at the bottom."""

    def __init__(self, result: ModelCheckResult) -> None:
        self.result = result

    def __rich__(self) -> Text:
        status_text = self.result.status.name
        if self.result.state == CheckState.Stopped:
            status_text = "canceled"
        elif self.result.state == CheckState.Success:
            status_text = "success"
        elif self.result.state == CheckState.Error:
            status_text = "failed"

        if not self.result.start_date_time:
            elapsed_str = "00:00:00"
            elapsed_style = "dim"
        else:
            if self.result.state == CheckState.Running:
                elapsed = datetime.now() - self.result.start_date_time
            else:
                elapsed = (self.result.end_date_time or datetime.now()) - self.result.start_date_time
            seconds = int(elapsed.total_seconds())
            hours, remainder = divmod(seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            elapsed_str = f"{hours:02}:{minutes:02}:{seconds:02}"
            elapsed_style = "bold cyan"

        footer = Text()
        footer.append("\n")
        footer.append("TLC Status: ", style="bold")
        footer.append(status_text, style="cyan")
        footer.append("\n")
        footer.append("Elapsed:  ", style="bold")
        footer.append(elapsed_str, style=elapsed_style)
        footer.append("\n")

        if self.result.state == CheckState.Running:
            footer.append("\n")
            footer.append("Stop with Ctrl + C", style="yellow")

        return footer
