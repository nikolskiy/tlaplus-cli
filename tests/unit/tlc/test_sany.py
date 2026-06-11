from tlaplus_cli.tlc.sany import SanyParser


def test_parse_sany_errors():
    parser = SanyParser()
    lines = [
        "Parsing file M.tla",
        "Semantic processing of module M",
        "*** Errors: 1",
        "line 10, col 5 to line 10, col 20 of module M",
        "Unknown operator 'foo'",
        "SANY finished.",
    ]
    for line in lines:
        parser.process_line(line)

    errors = parser.get_errors()
    assert len(errors) == 1
    err = errors[0]
    assert "Unknown operator 'foo'" in err.message
    assert err.module == "M"
    assert err.range_start_line == 10
    assert err.range_start_col == 5
    assert err.range_end_line == 10
    assert err.range_end_col == 20


def test_parse_sany_warnings():
    parser = SanyParser()
    lines = [
        "Parsing file M.tla",
        "*** Warnings: 1",
        "line 5, col 1 to line 5, col 10 of module M",
        "Warning message",
    ]
    for line in lines:
        parser.process_line(line)

    warnings = parser.get_warnings()
    assert len(warnings) == 1
    assert "Warning message" in warnings[0].message
