from typer.testing import CliRunner

from tlaplus_cli.cli import app

runner = CliRunner()


def test_tlc_help_coverage():
    """Test that tla tlc --help displays description and options."""
    result = runner.invoke(app, ["tlc", "--help"])
    assert result.exit_code == 0
    assert "--cleanup" in result.output
    assert "Purge" in result.output


def test_tlc_cleanup_command(mocker):
    """Test tla tlc --cleanup purges run cache."""
    mock_clear = mocker.patch("tlaplus_cli.cmd.tlc.clear_tlc_run_cache")
    result = runner.invoke(app, ["tlc", "--cleanup"])
    assert result.exit_code == 0
    assert "TLC run cache cleared successfully." in result.output
    mock_clear.assert_called_once()


def test_tlc_missing_spec_argument():
    """Test tla tlc without spec argument shows missing argument error."""
    result = runner.invoke(app, ["tlc"])
    assert result.exit_code == 1
    assert "Missing argument 'SPEC'." in result.output
