from src.tlaplus_cli.tlc.models import CheckState, CheckStatus
from src.tlaplus_cli.tlc.parser import TlcParser


def test_parse_starting():
    parser = TlcParser()
    parser.process_line("@!@!@STARTMSG 2185 @!@!@")
    parser.process_line("Starting... (2026-05-01 12:00:00)")
    parser.process_line("@!@!@ENDMSG 2185 @!@!@")

    result = parser.get_result()
    assert result.status == CheckStatus.Starting
    assert result.start_date_time is not None
    assert result.start_date_time.year == 2026
    assert result.start_date_time.month == 5
    assert result.start_date_time.day == 1


def test_parse_progress():
    parser = TlcParser()
    parser.process_line("@!@!@STARTMSG 2200 @!@!@")
    parser.process_line(
        "Progress(100) at 2026-05-01 12:00:05: 1,000 states generated, "
        "500 distinct states found, 100 states left on queue."
    )
    parser.process_line("@!@!@ENDMSG 2200 @!@!@")

    result = parser.get_result()
    assert len(result.initial_states_stat) == 1
    stat = result.initial_states_stat[0]
    assert stat.total == 1000
    assert stat.distinct == 500
    assert stat.queue_size == 100


def test_parse_error_trace():
    parser = TlcParser()
    # Error message
    parser.process_line("@!@!@STARTMSG 2110:1 @!@!@")
    parser.process_line("Invariant x = 0 is violated.")
    parser.process_line("@!@!@ENDMSG 2110 @!@!@")

    # State 1
    parser.process_line("@!@!@STARTMSG 2217 @!@!@")
    parser.process_line("1: <Initial predicate> line 5, col 1 to line 5, col 10 of module M")
    parser.process_line("x = 1")
    parser.process_line("@!@!@ENDMSG 2217 @!@!@")

    result = parser.get_result()
    assert result.state == CheckState.Error
    assert len(result.errors) == 1
    err = result.errors[0]
    assert len(err.error_trace) == 1
    state = err.error_trace[0]
    assert state.num == 1
    assert len(state.variables) == 1
    assert state.variables[0].key == "x"
    assert state.variables[0].value == "1"


def test_parse_finished():
    parser = TlcParser()
    parser.process_line("@!@!@STARTMSG 2186 @!@!@")
    parser.process_line("Finished in 123ms at (2026-05-01 12:00:10)")
    parser.process_line("@!@!@ENDMSG 2186 @!@!@")

    result = parser.get_result()
    assert result.status == CheckStatus.Finished
    assert result.duration == 123
    assert result.end_date_time is not None
    assert result.end_date_time.second == 10


def test_parse_coverage():
    parser = TlcParser()
    parser.process_line("@!@!@STARTMSG 2772 @!@!@")
    parser.process_line("<Next line 10, col 5 to line 10, col 20 of module M>: 100:50")
    parser.process_line("@!@!@ENDMSG 2772 @!@!@")

    result = parser.get_result()
    assert len(result.coverage_stat) == 1
    item = result.coverage_stat[0]
    assert item.module == "M"
    assert item.action == "Next"
    assert item.total == 100
    assert item.distinct == 50
