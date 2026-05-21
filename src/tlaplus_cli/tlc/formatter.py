from dataclasses import dataclass, field
from pathlib import Path

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from tlaplus_cli.tlc.models import (
    CoverageItem,
    ErrorTraceItem,
    ModelCheckResult,
    TlaValue,
)
from tlaplus_cli.tlc.sany import SanyMessage


@dataclass
class ValueDiff:
    key: str | int
    value: str
    tag: str  # "added", "modified", "unchanged"
    children: list["ValueDiff"] = field(default_factory=list)


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


class TlcFormatter:
    """Generates Rich layout for TLC model checking."""

    def __init__(self) -> None:
        self.info_dedup = LogDeduplicator()

    def render_sany_error(self, error: SanyMessage, spec_path: Path) -> Text:
        """Render SANY error with source code highlight."""
        result = Text()
        result.append(f"✖ SANY Error: {error.message}\n", style="bold red")
        result.append(f"  file://{spec_path}#L{error.range_start_line}\n\n", style="dim")

        if error.range_start_line is not None:
            try:
                with spec_path.open() as f:
                    lines = f.readlines()

                start_line = max(0, error.range_start_line - 3)
                end_line = min(len(lines), (error.range_end_line or error.range_start_line) + 2)

                for i in range(start_line, end_line):
                    line_num = i + 1
                    line_content = lines[i].rstrip()
                    if line_num == error.range_start_line:
                        result.append(f"{line_num:4} │ ", style="bold")
                        result.append(f"{line_content}\n")
                        # Add caret
                        col_start = error.range_start_col or 1
                        col_end = error.range_end_col or col_start + 1
                        caret_len = max(1, col_end - col_start)
                        caret_line = "     │ " + " " * (col_start - 1) + "▲" * caret_len
                        result.append(f"{caret_line}\n", style="bold red")
                        msg = f"line {error.range_start_line}, col {col_start} to {col_end}"
                        result.append(f"     │ {' ' * (col_start - 1)}└── Error here: {msg}\n", style="dim")
                    else:
                        result.append(f"{line_num:4} │ {line_content}\n", style="dim")

            except OSError:
                result.append("  (Source code unavailable)\n", style="dim")

        return result

    def diff_values(self, old_val: TlaValue | None, new_val: TlaValue) -> ValueDiff:
        """Recursively diff two TlaValue trees."""
        if old_val is None:
            return ValueDiff(
                key=new_val.key,
                value=new_val.value,
                tag="added",
                children=[self.diff_values(None, child) for child in new_val.children],
            )

        if old_val.value == new_val.value:
            return ValueDiff(
                key=new_val.key,
                value=new_val.value,
                tag="unchanged",
                children=[
                    self.diff_values(old_child, new_child)
                    for old_child, new_child in zip(old_val.children, new_val.children, strict=False)
                ],
            )

        # Values are different, but maybe some children are the same
        tag = "modified"
        children = []
        # Match children by key
        old_children_map = {c.key: c for c in old_val.children}
        for new_child in new_val.children:
            old_child = old_children_map.get(new_child.key)
            children.append(self.diff_values(old_child, new_child))

        return ValueDiff(
            key=new_val.key,
            value=new_val.value,
            tag=tag,
            children=children,
        )

    def render_value_diff(self, diff: ValueDiff, tree: Tree | None = None) -> Tree:
        """Render a ValueDiff into a Rich Tree."""
        style = ""
        prefix = ""
        if diff.tag == "added":
            style = "green"
            prefix = "[bold green]A[/] "
        elif diff.tag == "modified":
            style = "yellow"
            prefix = "[bold yellow]M[/] "
        elif diff.tag == "unchanged":
            style = "dim"

        label = Text()
        if prefix:
            label.append(Text.from_markup(prefix))
        label.append(f"{diff.key} = ")
        label.append(diff.value, style=style)

        node = Tree(label) if tree is None else tree.add(label)

        for child in diff.children:
            self.render_value_diff(child, node)

        return node

    def render_error_trace(self, trace: list[ErrorTraceItem]) -> Tree:
        """Render a full error trace as a Tree."""
        root = Tree("Counterexample (Error Trace)")
        last_variables: dict[str | int, TlaValue] = {}

        for item in trace:
            state_label = Text(f"State {item.num}: {item.action}")
            if item.module:
                state_label.append(f" in {item.module}", style="italic")

            state_node = root.add(state_label)

            # Sort variables to ensure consistent order
            sorted_vars = sorted(item.variables, key=lambda v: str(v.key))

            for var in sorted_vars:
                old_var = last_variables.get(var.key)
                diff = self.diff_values(old_var, var)
                self.render_value_diff(diff, state_node)
                last_variables[var.key] = var

        return root

    def render_coverage_table(self, coverage: list[CoverageItem]) -> Table:
        """Render action coverage table."""
        table = Table(title="Action Coverage", expand=True)
        table.add_column("Module")
        table.add_column("Action")
        table.add_column("Total States", justify="right")
        table.add_column("Unique States", justify="right")

        for item in coverage:
            table.add_row(
                item.module,
                item.action,
                f"{item.total:,}",
                f"{item.distinct:,}",
            )
        return table

    def render_inline_coverage(self, coverage: list[CoverageItem], spec_path: Path) -> Text:
        """Render inline spec coverage."""
        result = Text()
        result.append("\nInline Coverage View:\n", style="bold")
        result.append(" Coverage   Line │ Source Code\n", style="dim")
        result.append("─────────── ─────┼─────────────────────────────────────────────\n", style="dim")

        try:
            with spec_path.open() as f:
                lines = f.readlines()

            # Map lines to coverage
            line_coverage: dict[int, list[CoverageItem]] = {}
            for item in coverage:
                if item.module == spec_path.stem:
                    for line_idx in range(item.range_start_line, item.range_end_line + 1):
                        if line_idx not in line_coverage:
                            line_coverage[line_idx] = []
                        line_coverage[line_idx].append(item)

            for i, line_content in enumerate(lines):
                line_num = i + 1
                cov_items = line_coverage.get(line_num, [])

                cov_str = ""
                style = ""
                line_text = line_content.rstrip()
                if cov_items:
                    max_distinct = max(item.distinct for item in cov_items)
                    cov_str = f"{max_distinct:,}"
                    if max_distinct == 0:
                        style = "bold red"
                        line_text += "  <-- UNREACHED"

                result.append(f"{cov_str:>11} {line_num:5} │ ", style="dim")
                result.append(f"{line_text}\n", style=style)

        except OSError:
            result.append("  (Source code unavailable)\n", style="dim")

        return result

    def create_layout(self) -> Layout:
        """Create the initial layout structure."""
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
        )
        layout["body"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="logs", ratio=1),
        )
        return layout

    def update_header(self, layout: Layout, spec_name: str, result: ModelCheckResult) -> None:
        status_text = result.status.name
        duration = f"{result.duration}ms" if result.duration else "N/A"
        version = result.process_info or "unknown"

        header_text = Text.assemble(
            ("Running TLC Model Checker on Spec: ", "bold"),
            (f"{spec_name}.tla", "bold magenta"),
            ("\n"),
            (f"TLC version: {version} | Duration: {duration} | Status: {status_text}"),
        )
        layout["header"].update(Panel(header_text))

    def update_stats(self, layout: Layout, result: ModelCheckResult) -> None:
        table = Table(title="State Space Progress", expand=True)
        table.add_column("Time")
        table.add_column("Diameter", justify="right")
        table.add_column("Found", justify="right")
        table.add_column("Distinct", justify="right")
        table.add_column("Queue", justify="right")

        for item in result.initial_states_stat:
            table.add_row(
                item.timestamp,
                str(item.diameter),
                f"{item.total:,}",
                f"{item.distinct:,}",
                f"{item.queue_size:,}",
            )
        layout["stats"].update(Panel(table))

    def update_logs(self, layout: Layout, result: ModelCheckResult) -> None:
        deduped_logs: list[str] = []
        temp_dedup = LogDeduplicator()
        for line in result.output_lines:
            processed = temp_dedup.process(line)
            if temp_dedup.count > 1 and deduped_logs:
                deduped_logs[-1] = processed
            else:
                deduped_logs.append(processed)

        log_text = Text()
        for line in deduped_logs[-10:]:
            log_text.append(f"{line}\n")

        layout["logs"].update(Panel(log_text, title="LOGS (Warnings & Errors)"))
