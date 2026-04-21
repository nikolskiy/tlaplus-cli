from tlaplus_cli.config import loader as config


def test_config_paths(mocker, tmp_path):
    """Test config_dir, config_path, cache_dir return correct paths."""
    mocker.patch("platformdirs.user_config_dir", return_value=str(tmp_path / "config"))
    mocker.patch("platformdirs.user_cache_dir", return_value=str(tmp_path / "cache"))

    assert config.config_dir() == tmp_path / "config"
    assert config.config_path() == tmp_path / "config" / "config.yaml"
    assert config.cache_dir() == tmp_path / "cache"


def test_ensure_config_creates_default(mocker, tmp_path):
    """ensure_config creates the config file if it doesn't exist."""
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)
    config_path = config_dir / "config.yaml"

    assert not config_path.exists()
    path = config.ensure_config()
    assert path == config_path
    assert config_path.exists()
    assert "workspace:" in config_path.read_text()


def test_load_config_caching(mocker, tmp_path):
    """load_config should be cached."""
    config.load_config.cache_clear()

    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)
    config.ensure_config()

    # First call
    c1 = config.load_config()
    # Second call should return the same object from cache
    c2 = config.load_config()
    assert c1 is c2


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
