from tlaplus_cli.tlc.values import parse_variable_value


def test_parse_primitive_int():
    val = parse_variable_value("x", ["42"])
    assert val.key == "x"
    assert val.value == "42"


def test_parse_primitive_string():
    val = parse_variable_value("x", ['"hello"'])
    assert val.value == '"hello"'


def test_parse_primitive_bool():
    val = parse_variable_value("x", ["TRUE"])
    assert val.value == "TRUE"


def test_parse_set():
    val = parse_variable_value("x", ["{1, 2, 3}"])
    assert val.value == "{1, 2, 3}"
    assert len(val.children) == 3
    assert val.children[0].value == "1"
    assert val.children[1].value == "2"
    assert val.children[2].value == "3"


def test_parse_sequence():
    val = parse_variable_value("x", ["<<1, 2>>"])
    assert val.value == "<<1, 2>>"
    assert len(val.children) == 2


def test_parse_structure():
    val = parse_variable_value("x", ["[a |-> 1, b |-> 2]"])
    assert val.value == "[a |-> 1, b |-> 2]"
    assert len(val.children) == 2
    assert val.children[0].key == "a"
    assert val.children[0].value == "1"
    assert val.children[1].key == "b"
    assert val.children[1].value == "2"


def test_parse_nested():
    val = parse_variable_value("x", ["{[a |-> <<1>>]}"])
    assert len(val.children) == 1
    struct = val.children[0]
    assert len(struct.children) == 1
    seq = struct.children[0]
    assert len(seq.children) == 1
    assert seq.children[0].value == "1"
