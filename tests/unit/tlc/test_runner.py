from unittest.mock import MagicMock

import pytest

from tlaplus_cli.tlc.runner import build_tlc_command, resolve_cfg_file, run_tlc


def test_run_tlc_keyboard_interrupt(mocker):
    """Test that run_tlc handles KeyboardInterrupt gracefully."""
    # Mock subprocess.Popen
    mock_process = MagicMock()
    # Popen used as context manager returns the process object from __enter__
    mock_process.__enter__.return_value = mock_process
    mock_process.stdout = ["line 1\n", "line 2\n"]
    mock_process.returncode = 0

    # We want to raise KeyboardInterrupt during iteration
    def side_effect():
        yield "line 1\n"
        raise KeyboardInterrupt()

    mock_process.stdout = side_effect()

    mocker.patch("subprocess.Popen", return_value=mock_process)
    mocker.patch("tlaplus_cli.tlc.runner.load_config")
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")
    mocker.patch("tlaplus_cli.tlc.runner.resolve_spec_file", return_value=(MagicMock(), "Spec"))
    mocker.patch("tlaplus_cli.tlc.runner.build_tlc_command", return_value=["java", "tlc2.TLC", "Spec"])

    callback = MagicMock()

    # We expect run_tlc to catch KeyboardInterrupt and return exit code
    exit_code = run_tlc("Spec", callback=callback)

    assert exit_code == 0
    mock_process.terminate.assert_called_once()
    # It should have called callback at least once before interrupt
    assert callback.called


def test_build_tlc_command_includes_metadir(tmp_path, mocker):
    """Test that build_tlc_command appends -metadir <run_dir>."""
    spec_file = tmp_path / "MySpec.tla"
    spec_file.write_text("---- MODULE MySpec ----\n====\n")

    mocker.patch("tlaplus_cli.tlc.runner.get_tlc_jar_path", return_value=tmp_path / "tla2tools.jar")
    (tmp_path / "tla2tools.jar").touch()

    mocker.patch("tlaplus_cli.tlc.runner.resolve_spec_file", return_value=(spec_file, "MySpec.tla"))
    mocker.patch("tlaplus_cli.tlc.runner.find_project_root", return_value=None)

    cmd = build_tlc_command(str(spec_file))

    assert "-metadir" in cmd
    metadir_idx = cmd.index("-metadir")
    assert metadir_idx + 1 < len(cmd)
    assert "MySpec_" in cmd[metadir_idx + 1]


def test_resolve_cfg_file_with_extension(tmp_path):
    """Test resolve_cfg_file finds .cfg file when extension is provided."""
    spec_file = tmp_path / "MySpec.tla"
    cfg_file = tmp_path / "MySpec-v1.cfg"
    cfg_file.write_text("SPECIFICATION Spec\n")

    resolved_path, cfg_arg = resolve_cfg_file("MySpec-v1.cfg", spec_file)
    assert resolved_path == cfg_file.absolute()
    assert cfg_arg == "MySpec-v1.cfg"


def test_resolve_cfg_file_without_extension(tmp_path):
    """Test resolve_cfg_file automatically appends .cfg when omitted."""
    spec_file = tmp_path / "MySpec.tla"
    cfg_file = tmp_path / "MySpec-v2.cfg"
    cfg_file.write_text("SPECIFICATION Spec\n")

    resolved_path, cfg_arg = resolve_cfg_file("MySpec-v2", spec_file)
    assert resolved_path == cfg_file.absolute()
    assert cfg_arg == "MySpec-v2.cfg"


def test_resolve_cfg_file_not_found(tmp_path):
    """Test resolve_cfg_file raises FileNotFoundError when .cfg file does not exist."""
    spec_file = tmp_path / "MySpec.tla"

    with pytest.raises(FileNotFoundError, match="Could not find TLC configuration file"):
        resolve_cfg_file("NonExistent", spec_file)


def test_build_tlc_command_with_cfg(tmp_path, mocker):
    """Test build_tlc_command includes -config <cfg_file> when cfg option is specified."""
    spec_file = tmp_path / "MySpec.tla"
    spec_file.write_text("---- MODULE MySpec ----\n====\n")
    cfg_file = tmp_path / "MySpec-v1.cfg"
    cfg_file.write_text("SPECIFICATION Spec\n")

    mocker.patch("tlaplus_cli.tlc.runner.get_tlc_jar_path", return_value=tmp_path / "tla2tools.jar")
    (tmp_path / "tla2tools.jar").touch()

    mocker.patch("tlaplus_cli.tlc.runner.resolve_spec_file", return_value=(spec_file, "MySpec.tla"))
    mocker.patch("tlaplus_cli.tlc.runner.find_project_root", return_value=None)

    cmd = build_tlc_command(str(spec_file), cfg="MySpec-v1")

    assert "-config" in cmd
    config_idx = cmd.index("-config")
    assert config_idx + 1 < len(cmd)
    assert cmd[config_idx + 1] == "MySpec-v1.cfg"


