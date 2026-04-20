from tlaplus_cli import config
from tlaplus_cli.cli import app


def test_modules_lib_view_custom(mocker, tmp_path, runner):
    """Test viewing a custom modules lib path."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    lib_dir = tmp_path / "my_libs"
    lib_dir.mkdir()

    # Set it first
    runner.invoke(app, ["modules", "lib", str(lib_dir)])

    # View it
    result = runner.invoke(app, ["modules", "lib"])
    assert result.exit_code == 0
    assert f"Current modules lib path: {lib_dir}" in result.output


def test_modules_lib_view_default(mocker, tmp_path, runner):
    """Test viewing the default modules lib path when none is set."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)
    mocker.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=tmp_path)

    # Ensure it's None
    cfg = config.load_config()
    cfg.module_path = None
    cfg.module_lib_path = None
    config.save_config(cfg)

    # If module_path is None, it defaults to workspace_root / modules_dir / lib
    expected_default = tmp_path / cfg.workspace.modules_dir / "lib"

    result = runner.invoke(app, ["modules", "lib"])
    assert result.exit_code == 0
    assert "Custom modules lib path is not set" in result.output
    assert f"Defaulting to: {expected_default}" in result.output


def test_modules_lib_view_default_with_custom_module_path(mocker, tmp_path, runner):
    """Test viewing the default modules lib path when custom module_path is set."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    module_dir = tmp_path / "custom_modules"
    module_dir.mkdir()

    cfg = config.load_config()
    cfg.module_path = str(module_dir)
    cfg.module_lib_path = None
    config.save_config(cfg)

    expected_default = module_dir / "lib"

    result = runner.invoke(app, ["modules", "lib"])
    assert result.exit_code == 0
    assert "Custom modules lib path is not set" in result.output
    assert f"Defaulting to: {expected_default}" in result.output


def test_modules_lib_set(mocker, tmp_path, runner):
    """Test setting the modules lib path."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    lib_dir = tmp_path / "my_libs"
    lib_dir.mkdir()

    result = runner.invoke(app, ["modules", "lib", str(lib_dir)])
    assert result.exit_code == 0
    assert f"Modules lib path updated to: {lib_dir}" in result.output

    # Check config
    config.load_config.cache_clear()
    cfg = config.load_config()
    assert cfg.module_lib_path == str(lib_dir)


def test_modules_lib_reset(mocker, tmp_path, runner):
    """Test resetting the modules lib path."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)

    lib_dir = tmp_path / "my_libs"
    lib_dir.mkdir()

    # Set it first
    runner.invoke(app, ["modules", "lib", str(lib_dir)])

    # Reset it
    result = runner.invoke(app, ["modules", "lib", "none"])
    assert result.exit_code == 0
    assert "Custom modules lib path reset to default" in result.output

    # Check config
    config.load_config.cache_clear()
    cfg = config.load_config()
    assert cfg.module_lib_path is None
