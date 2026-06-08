from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Group
from rich.layout import Layout
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from tlaplus_cli.tlc.components import (
    HeaderComponent,
    LogDeduplicator,
    LogsComponent,
    StatsTableComponent,
    StatusInfoComponent,
)
from tlaplus_cli.tlc.models import (
    CoverageItem,
    ErrorTraceItem,
    ModelCheckResult,
    TlaValue,
)
from tlaplus_cli.tlc.sany import SanyMessage


@dataclass
class _Section:
    """A named section in the TLC display."""

    name: str
    renderable: Any = field(default_factory=lambda: Text(""))
    size: int | None = None

    def update(self, renderable: Any) -> None:
        """Update the section content."""
        self.renderable = renderable

    def __rich__(self) -> Any:
        return self.renderable


class TlcDisplay:
    """A dynamic display that grows as content is added."""

    def __init__(self) -> None:
        self.children: list[_Section] = []
        self.renderable: Any = Text("")

    def __getitem__(self, name: str) -> _Section:
        for child in self.children:
            if child.name == name:
                return child
        raise KeyError(name)

    def update(self, renderable: Any) -> None:
        """Update root renderable (used before splitting)."""
        self.renderable = renderable

    def split_column(self, *sections: _Section) -> None:
        """Set the active sections."""
        self.children = list(sections)

    def __rich__(self) -> Group:
        if not self.children:
            return Group(self.renderable)
        return Group(*self.children)


@dataclass
class ValueDiff:
    key: str | int
    value: str
    tag: str  # "added", "modified", "unchanged"
    children: list["ValueDiff"] = field(default_factory=list)


class TlcFormatter:
    """Generates Rich layout for TLC model checking."""

    def __init__(self, tlc_version: str = "unknown") -> None:
        self.info_dedup = LogDeduplicator()
        self.tlc_version = tlc_version
        self.header_comp = HeaderComponent(tlc_version)
        self.status_info_comp = StatusInfoComponent()
        self.logs_comp = LogsComponent(limit=10)
        self.stats_comp = StatsTableComponent()

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

    def create_layout(self) -> Any:
        """Create the initial layout structure with only the header."""
        layout = TlcDisplay()
        layout.update(self.header_comp.render(ModelCheckResult()))
        return layout

    def update(self, layout: Any, result: ModelCheckResult) -> None:
        """Main update entry point that manages layout structure and content."""
        self._ensure_layout_structure(layout, result)
        self.update_header(layout, result)
        if self._has_child(layout, "clock"):
            self.update_clock(layout, result)
        if self._has_child(layout, "logs"):
            self.update_logs(layout, result)
        if self._has_child(layout, "stats"):
            self.update_stats(layout, result)

    def _has_child(self, layout: Any, name: str) -> bool:
        """Check if a layout has a child with the given name."""
        return any(child.name == name for child in layout.children)

    def _ensure_layout_structure(self, layout: Any, result: ModelCheckResult) -> None:
        """Dynamically add sections as data becomes available."""
        has_logs = bool(result.output_lines)
        has_stats = bool(result.initial_states_stat)
        has_clock = bool(result.start_date_time or result.process_info or result.duration)

        # Build expected structure in desired order:
        # 1. Header
        # 2. Status Info (clock)
        # 3. TLC instance info (logs)
        # 4. State Space Progress (stats) - grows infinitely at the bottom
        new_layouts = [_Section(name="header", size=2)]
        if has_clock:
            new_layouts.append(_Section(name="clock", size=7))
        if has_logs:
            new_layouts.append(_Section(name="logs"))
        if has_stats:
            new_layouts.append(_Section(name="stats"))

        # Check if we need to update
        current_names = [lay.name for lay in layout.children]
        expected_names = [lay.name for lay in new_layouts]

        if current_names != expected_names:
            layout.split_column(*new_layouts)

    def update_header(self, layout: Any, result: ModelCheckResult) -> None:
        """Update header."""
        header_text = self.header_comp.render(result)
        if self._has_child(layout, "header"):
            layout["header"].update(header_text)
        else:
            layout.update(header_text)

    def update_stats(self, layout: Layout, result: ModelCheckResult) -> None:
        table = self.stats_comp.render(result)
        layout["stats"].update(table)

    def update_logs(self, layout: Layout, result: ModelCheckResult) -> None:
        """Update logs panel with TLC output."""
        group = self.logs_comp.render(result)
        layout["logs"].update(group)

    def update_clock(self, layout: Layout, result: ModelCheckResult) -> None:
        """Update info panel at the bottom with clock and TLC stats."""
        layout["clock"].update(StatusInfoRenderable(result))


class StatusInfoRenderable:
    """Renderable that computes elapsed time dynamically."""

    def __init__(self, result: ModelCheckResult) -> None:
        self.result = result

    def __rich__(self) -> Group:
        """Render the status info group."""
        comp = StatusInfoComponent()
        return comp.render(self.result)
