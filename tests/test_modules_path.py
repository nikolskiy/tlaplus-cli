from tlaplus_cli import config
from tlaplus_cli.cli import app


def test_modules_path_success(mocker, tmp_path, runner):
    """Test successful setting of modules path."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    # Create a dummy module directory
    module_dir = tmp_path / "my_modules"
    module_dir.mkdir()

    result = runner.invoke(app, ["modules", "path", str(module_dir)])

    assert result.exit_code == 0
    assert f"Modules path updated to: {module_dir}" in result.output

    # Check config
    config.load_config.cache_clear()
    cfg = config.load_config()
    assert cfg.module_path == str(module_dir)


def test_modules_path_invalid_dir(mocker, tmp_path, runner):
    """Test setting modules path to non-existent directory fails."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    invalid_dir = tmp_path / "does_not_exist"

    result = runner.invoke(app, ["modules", "path", str(invalid_dir)])

    assert result.exit_code == 1
    assert "Error: Path does not exist or is not a directory" in result.output

    # Check config was NOT updated
    config.load_config.cache_clear()
    cfg = config.load_config()
    assert cfg.module_path is None


def test_modules_path_file_instead_of_dir(mocker, tmp_path, runner):
    """Test setting modules path to a file fails."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    some_file = tmp_path / "some_file.txt"
    some_file.write_text("hello")

    result = runner.invoke(app, ["modules", "path", str(some_file)])

    assert result.exit_code == 1
    assert "Error: Path does not exist or is not a directory" in result.output

    # Check config was NOT updated
    config.load_config.cache_clear()
    cfg = config.load_config()
    assert cfg.module_path is None
