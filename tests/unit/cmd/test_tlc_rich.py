from typer.testing import CliRunner

from tlaplus_cli.cli import app
from tlaplus_cli.config.schema import TlcConfig

runner = CliRunner()


def test_tlc_refresh_interval_option():
    """Test that --refresh-interval option is accepted by the tlc command."""
    # We use a non-existent spec to fail fast, but we check if the option is recognized
    result = runner.invoke(app, ["tlc", "NonExistentSpec", "--refresh-interval", "2.5"])
    # It should not say "no such option"
    assert "No such option: --refresh-interval" not in result.output
    # It will fail with FileNotFoundError because NonExistentSpec doesn't exist, which is expected
    assert "Error: Could not find a TLA+ spec file for 'NonExistentSpec'" in result.output


def test_tlc_config_refresh_interval():
    """Test that TlcConfig has refresh_interval field."""
    config = TlcConfig()
    assert config.refresh_interval == 1.0

    config = TlcConfig(refresh_interval=2.0)
    assert config.refresh_interval == 2.0
