from tlaplus_cli.cli import app
from tlaplus_cli.config import loader as config


def test_config_list(mocker, tmp_path, runner):
    """Test listing the configuration."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    result = runner.invoke(app, ["config", "list"])
    assert result.exit_code == 0
    # It should contain some keys from the default config
    assert "workspace:" in result.output
    assert "tlc:" in result.output

def test_config_edit_default(mocker, tmp_path, runner):
    """Test launching default editor for config."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    # Mock shutil.which to find 'vim' as default
    mocker.patch(
        "tlaplus_cli.cmd.config.edit.shutil.which",
        side_effect=lambda x: f"/usr/bin/{x}" if x == "vim" else None,
    )
    # Mock subprocess.run
    mock_run = mocker.patch("tlaplus_cli.cmd.config.edit.subprocess.run")
    # Set EDITOR env var
    mocker.patch.dict("os.environ", {"EDITOR": "vim"})

    result = runner.invoke(app, ["config", "edit"])
    assert result.exit_code == 0, result.output

    # Verify subprocess.run was called with vim and the config path
    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    assert args[0][0] == "/usr/bin/vim"
    assert str(config_dir / "config.yaml") in args[0]

def test_config_edit_specific_editor(mocker, tmp_path, runner):
    """Test launching a specific editor."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    mocker.patch("tlaplus_cli.cmd.config.edit.shutil.which", return_value="/usr/bin/nano")
    mock_run = mocker.patch("tlaplus_cli.cmd.config.edit.subprocess.run")

    result = runner.invoke(app, ["config", "edit", "nano"])
    assert result.exit_code == 0

    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    assert args[0][0] == "/usr/bin/nano"
    assert str(config_dir / "config.yaml") in args[0]

def test_config_edit_missing_editor(mocker, tmp_path, runner):
    """Test error when editor is not found."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    mocker.patch("tlaplus_cli.cmd.config.edit.shutil.which", return_value=None)
    mock_run = mocker.patch("tlaplus_cli.cmd.config.edit.subprocess.run")

    result = runner.invoke(app, ["config", "edit", "nonexistent-editor"])
    assert result.exit_code == 1
    assert "Error: Editor 'nonexistent-editor' not found" in result.output
    mock_run.assert_not_called()
