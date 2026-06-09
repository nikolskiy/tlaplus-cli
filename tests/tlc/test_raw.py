from pathlib import Path
from unittest.mock import MagicMock

from tlaplus_cli.tlc.runner import build_tlc_command, run_tlc


def test_build_tlc_command_relative_path(mocker):
    # Mock dependencies
    mocker.patch("tlaplus_cli.tlc.runner.load_config")

    mock_jar = mocker.patch("tlaplus_cli.tlc.runner.get_tlc_jar_path")
    mock_jar.return_value.exists.return_value = True
    mock_jar.return_value.absolute.return_value = Path("/mock/tla2tools.jar")

    # The spec file is /workspace/project/tests/Spec.tla
    mocker.patch(
        "tlaplus_cli.tlc.runner.resolve_spec_file", return_value=(Path("/workspace/project/tests/Spec.tla"), "Spec.tla")
    )
    # Project root is /workspace/project
    mocker.patch("tlaplus_cli.tlc.runner.find_project_root", return_value=Path("/workspace/project"))

    # ClasspathResolver mock
    mock_resolver_cls = mocker.patch("tlaplus_cli.tlc.runner.ClasspathResolver")
    mock_resolver = MagicMock()
    mock_resolver.resolve.return_value = ["/mock/classes", "/mock/tla2tools.jar"]
    mock_resolver.get_tla_library_property.return_value = "/mock/modules"
    mock_resolver_cls.return_value = mock_resolver

    cmd = build_tlc_command("tests/Spec.tla")
    # Verify that the spec file argument is relative to project root: "tests/Spec.tla"
    assert cmd[-1] == "tests/Spec.tla"


def test_run_tlc_raw(mocker, capsys):
    # Mock build_tlc_command to return a mock command
    mocker.patch(
        "tlaplus_cli.tlc.runner.build_tlc_command",
        return_value=["java", "-cp", "class.jar", "tlc2.TLC", "tests/Spec.tla"],
    )

    # Mock config loader and java version validation
    mocker.patch("tlaplus_cli.tlc.runner.load_config")
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    mocker.patch(
        "tlaplus_cli.tlc.runner.resolve_spec_file", return_value=(Path("/workspace/project/tests/Spec.tla"), "Spec.tla")
    )
    mocker.patch("tlaplus_cli.tlc.runner.find_project_root", return_value=Path("/workspace/project"))

    # Mock subprocess.Popen
    mock_process = MagicMock()
    mock_process.__enter__.return_value = mock_process
    mock_process.stdout = ["raw line 1\n", "raw line 2\n"]
    mock_process.returncode = 0
    mock_popen = mocker.patch("subprocess.Popen", return_value=mock_process)

    exit_code = run_tlc("tests/Spec.tla", raw=True)

    assert exit_code == 0
    # Verify Popen was called with correct command (no -tool inserted) and cwd = project_root
    mock_popen.assert_called_once()
    called_cmd = mock_popen.call_args[0][0]
    assert "-tool" not in called_cmd
    assert mock_popen.call_args[1]["cwd"] == "/workspace/project"

    # Verify output was streamed to sys.stdout
    captured = capsys.readouterr()
    assert "raw line 1\n" in captured.out
    assert "raw line 2\n" in captured.out
