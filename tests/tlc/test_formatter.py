from datetime import datetime, timedelta

from rich.table import Table

from tlaplus_cli.tlc.formatter import LogDeduplicator, TlcFormatter
from tlaplus_cli.tlc.models import (
    CheckStatus,
    CoverageItem,
    InitialStateStatItem,
    ModelCheckResult,
    TlaValue,
)
from tlaplus_cli.tlc.sany import SanyMessage


def test_log_deduplicator():
    dedup = LogDeduplicator()

    # First message
    assert dedup.process("Message 1") == "Message 1"

    # Duplicate message
    assert dedup.process("Message 1") == "Message 1 (2)"

    # Another duplicate
    assert dedup.process("Message 1") == "Message 1 (3)"

    # Different message resets
    assert dedup.process("Message 2") == "Message 2"

    # New duplicate
    assert dedup.process("Message 2") == "Message 2 (2)"


def test_log_deduplicator_strip():
    dedup = LogDeduplicator()
    assert dedup.process("  Message 1  ") == "Message 1"
    assert dedup.process("Message 1") == "Message 1 (2)"


def test_update_stats():
    formatter = TlcFormatter()
    layout = formatter.create_layout()
    result = ModelCheckResult()
    result.initial_states_stat = [
        InitialStateStatItem("00:00:01", 2, 50, 30, 10),
        InitialStateStatItem("00:00:02", 5, 200, 120, 40),
    ]

    formatter.update(layout, result)

    # Check if layout was updated with a table
    table = layout["stats"].renderable
    assert isinstance(table, Table)
    assert table.title == "State Space Progress"
    assert len(table.rows) == 2
    assert table.columns[0].header == "Time"
    assert table.columns[1].header == "Diameter"
    assert table.columns[2].header == "Found"
    assert table.columns[3].header == "Distinct"
    assert table.columns[4].header == "Queue"


def test_tla_value_diffing():
    formatter = TlcFormatter()

    val1 = TlaValue("x", "1")
    val2 = TlaValue("x", "2")

    # Simple modification
    diff = formatter.diff_values(val1, val2)
    assert diff.tag == "modified"

    # Unchanged
    val3 = TlaValue("y", "true")
    val4 = TlaValue("y", "true")
    diff = formatter.diff_values(val3, val4)
    assert diff.tag == "unchanged"

    # Nested modification
    val_nested1 = TlaValue("rec", "[a |-> 1, b |-> 2]", [TlaValue("a", "1"), TlaValue("b", "2")])
    val_nested2 = TlaValue("rec", "[a |-> 1, b |-> 3]", [TlaValue("a", "1"), TlaValue("b", "3")])
    diff = formatter.diff_values(val_nested1, val_nested2)
    assert diff.tag == "modified"
    assert diff.children[0].tag == "unchanged"
    assert diff.children[1].tag == "modified"


def test_render_sany_error(tmp_path):
    formatter = TlcFormatter()
    spec_path = tmp_path / "Test.tla"
    spec_path.write_text("MODULE Test\nINIT == x = 0\nNEXT == x' = x + 1\n")

    error = SanyMessage(
        message="Some error", module="Test", range_start_line=2, range_start_col=9, range_end_line=2, range_end_col=10
    )

    rendered = formatter.render_sany_error(error, spec_path)
    rendered_str = rendered.plain

    assert "✖ SANY Error: Some error" in rendered_str
    assert "2 │ INIT == x = 0" in rendered_str
    assert "▲" in rendered_str


def test_render_coverage(tmp_path):
    formatter = TlcFormatter()
    spec_path = tmp_path / "Test.tla"
    spec_path.write_text("MODULE Test\nINIT == x = 0\nNEXT == x' = x + 1\n")

    coverage = [
        CoverageItem("Test", "INIT", None, 2, 1, 2, 10, 1, 1),
        CoverageItem("Test", "NEXT", None, 3, 1, 3, 10, 0, 0),
    ]

    # Table
    table = formatter.render_coverage_table(coverage)
    assert table.title == "Action Coverage"
    assert len(table.rows) == 2

    # Inline
    rendered = formatter.render_inline_coverage(coverage, spec_path)
    rendered_str = rendered.plain
    assert "1     2 │ INIT == x = 0" in rendered_str
    assert "0     3 │ NEXT == x' = x + 1  <-- UNREACHED" in rendered_str


def test_update_header():
    formatter = TlcFormatter()
    layout = formatter.create_layout()
    result = ModelCheckResult()
    result.status = CheckStatus.Starting
    result.process_info = "2.18"
    result.duration = 1234

    formatter.update(layout, result)

    header_text = layout["header"].renderable.plain

    assert "Starting TLC model checker." in header_text
    # These should NOT be in the header anymore
    assert "TLC version: 2.18" not in header_text
    assert "Duration: 1234ms" not in header_text
    assert "Status: Starting" not in header_text


def test_update_logs():
    formatter = TlcFormatter()
    layout = formatter.create_layout()
    result = ModelCheckResult()
    result.output_lines = ["Line 1", "Line 2"]

    formatter.update(layout, result)

    group = layout["logs"].renderable
    assert "TLC instance info" in group.renderables[0].renderable.plain
    assert "Line 1" in group.renderables[1].plain
    assert "Line 2" in group.renderables[1].plain


def test_update_clock():
    formatter = TlcFormatter()
    layout = formatter.create_layout()
    result = ModelCheckResult()
    result.status = CheckStatus.Starting
    result.process_info = "2.18"
    result.duration = 1234
    result.start_date_time = datetime.now() - timedelta(seconds=65)

    formatter.update(layout, result)

    clock_text = layout["clock"].renderable.plain
    assert "Elapsed time: 00:01:05" in clock_text
    assert "TLC version: 2.18" in clock_text
    assert "Duration: 1234ms" in clock_text
    assert "Status: Starting" in clock_text
    assert "Stop with Ctrl + C" in clock_text


def test_initial_layout_state():
    formatter = TlcFormatter()
    layout = formatter.create_layout()

    # Only one child initially (not yet split)
    assert len(layout.children) == 0
    assert "Starting TLC model checker." in layout.renderable.plain

    # Add logs
    result = ModelCheckResult()
    result.output_lines = ["log"]
    formatter.update(layout, result)

    assert "header" in [lay.name for lay in layout.children]
    assert "logs" in [lay.name for lay in layout.children]
    assert "stats" not in [lay.name for lay in layout.children]
    assert "clock" not in [lay.name for lay in layout.children]

    # Add stats
    result.initial_states_stat = [InitialStateStatItem("00:00:01", 1, 1, 1, 1)]
    formatter.update(layout, result)
    assert "stats" in [lay.name for lay in layout.children]

    # Add clock info
    result.process_info = "2.18"
    formatter.update(layout, result)
    assert "clock" in [lay.name for lay in layout.children]
