"""The tla command prints the rename notice and forwards to tlaup."""

import pytest

from tlaplus_cli import cli


def test_prints_notice_on_stderr_and_forwards(mocker: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    forwarded = mocker.patch("tlaup.cli.main")
    cli.main()
    captured = capsys.readouterr()
    assert "tlaup" in captured.err
    assert "uv tool install tlaup" in captured.err
    assert captured.out == ""
    forwarded.assert_called_once_with()


def test_forwards_arguments_unchanged(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr("sys.argv", ["tla", "--version"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("tlaup v")
    assert "tlaplus-cli is now called tlaup" in captured.err
