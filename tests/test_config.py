from tlaplus_cli import config


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
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)
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
    mocker.patch("tlaplus_cli.config.config_dir", return_value=config_dir)
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
    mocker.patch("tlaplus_cli.config.load_config", return_value=mock_settings)

    assert config.workspace_root() == abs_path


def test_workspace_root_relative(mocker, tmp_path, monkeypatch):
    """workspace_root resolves relative path from CWD."""
    monkeypatch.chdir(tmp_path)
    mock_settings = mocker.MagicMock()
    mock_settings.workspace.root = "relative_ws"
    mocker.patch("tlaplus_cli.config.load_config", return_value=mock_settings)

    assert config.workspace_root() == tmp_path / "relative_ws"
