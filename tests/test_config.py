from tlaplus_cli.config import loader as config


def test_config_paths(mocker, tmp_path):
    """Test config_dir, config_path, cache_dir return correct paths."""
    mocker.patch("platformdirs.user_config_dir", return_value=str(tmp_path / "config"))
    mocker.patch("platformdirs.user_cache_dir", return_value=str(tmp_path / "cache"))

    assert config.config_dir() == tmp_path / "config"
    assert config.config_path() == tmp_path / "config" / "config.yaml"
    assert config.cache_dir() == tmp_path / "cache"


def test_ensure_config_creates_default(mocker, tmp_path):
    """_ensure_config creates the config file if it doesn't exist."""
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)
    config_path = config_dir / "config.yaml"

    assert not config_path.exists()
    path = config._ensure_config()
    assert path == config_path
    assert config_path.exists()
    assert "workspace:" in config_path.read_text()


def test_load_config_caching(mocker, tmp_path):
    """load_config should be cached."""
    config.load_config.cache_clear()

    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)
    config._ensure_config()

    # First call
    c1 = config.load_config()
    # Second call should return the same object from cache
    c2 = config.load_config()
    assert c1 is c2


def test_workspace_root_absolute(mocker, tmp_path):
    """workspace_root returns absolute path when config has absolute path."""
    abs_path = (tmp_path / "my_ws").absolute()
    mock_settings = mocker.MagicMock()
    mock_settings.workspace.root = str(abs_path)
    mocker.patch("tlaplus_cli.config.loader.load_config", return_value=mock_settings)

    assert config.workspace_root() == abs_path


def test_load_module_path(mocker, tmp_path):
    """Test that module_path can be loaded from config."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)
    config_path = config_dir / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    config_content = """
tla:
  urls:
    tags: https://example.com/tags
    releases: https://example.com/releases
    per_page: 30
workspace:
  root: .
  spec_dir: spec
  modules_dir: modules
  classes_dir: classes
tlc:
  java_class: tlc2.TLC
  overrides_class: tlc2.overrides.TLCOverrides
module_path: /custom/path
"""
    config_path.write_text(config_content)

    cfg = config.load_config()
    assert cfg.module_path == "/custom/path"


def test_save_config(mocker, tmp_path):
    """Test saving config preserves module_path and uses deep copy."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)
    config_path = config_dir / "config.yaml"
    config_dir.mkdir(parents=True, exist_ok=True)

    cfg = config.load_config()
    cfg.module_path = "/new/path"

    config.save_config(cfg)

    # Reload and check
    config.load_config.cache_clear()
    new_cfg = config.load_config()
    assert new_cfg.module_path == "/new/path"
    assert "module_path: /new/path" in config_path.read_text()
