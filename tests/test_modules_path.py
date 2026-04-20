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


def test_modules_path_view_custom(mocker, tmp_path, runner):
    """Test viewing a custom modules path."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    module_dir = tmp_path / "my_modules"
    module_dir.mkdir()

    # Set it first
    runner.invoke(app, ["modules", "path", str(module_dir)])

    # View it
    result = runner.invoke(app, ["modules", "path"])
    assert result.exit_code == 0
    assert f"Current modules path: {module_dir}" in result.output


def test_modules_path_view_default(mocker, tmp_path, runner):
    """Test viewing the default modules path when none is set."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=tmp_path)

    # Ensure it's None
    cfg = config.load_config()
    cfg.module_path = None
    config.save_config(cfg)

    result = runner.invoke(app, ["modules", "path"])
    assert result.exit_code == 0
    assert "Custom modules path is not set" in result.output
    assert f"Defaulting to: {tmp_path / cfg.workspace.modules_dir}" in result.output


def test_modules_path_reset(mocker, tmp_path, runner):
    """Test resetting the custom modules path."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    module_dir = tmp_path / "my_modules"
    module_dir.mkdir()

    # Set it first
    runner.invoke(app, ["modules", "path", str(module_dir)])

    # Reset it
    result = runner.invoke(app, ["modules", "path", "none"])
    assert result.exit_code == 0
    assert "Custom modules path reset to default" in result.output

    # Check config
    config.load_config.cache_clear()
    cfg = config.load_config()
    assert cfg.module_path is None
