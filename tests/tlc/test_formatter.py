from tlaplus_cli.tlc.formatter import LogDeduplicator, TlcFormatter
from tlaplus_cli.tlc.models import (
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

    formatter.update_stats(layout, result)

    # Check if layout was updated with a table
    stats_panel = layout["stats"].renderable
    table = stats_panel.renderable
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
