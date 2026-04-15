import json
from pathlib import Path

from tlaplus_cli.cli import app


def test_tlc_path_pinned_with_metadata(mock_load_config, mock_cache, installed_v180, runner):
    """path strictly outputs the absolute path to tla2tools.jar, even if metadata exists."""
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")
    # Write metadata
    meta = {"tlc2_version_string": "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"}
    (installed_v180 / "meta-tla2tools.json").write_text(json.dumps(meta))

    result = runner.invoke(app, ["tools", "path"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "tla2tools.jar" in lines[0]
    assert Path(lines[0]).is_absolute()
    assert "TLC2 Version" not in result.stdout


def test_tlc_path_pinned_without_metadata(mock_load_config, mock_cache, installed_v180, runner):
    """path strictly outputs the absolute path to tla2tools.jar when no metadata exists."""
    pin_file = mock_cache / "tools" / "tools-pinned-version.txt"
    pin_file.write_text("v1.8.0-aaaaaaa")

    result = runner.invoke(app, ["tools", "path"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "tla2tools.jar" in lines[0]
    assert Path(lines[0]).is_absolute()


def test_tlc_path_version_with_metadata(mock_load_config, mock_cache, installed_v180, runner):
    """path <version> strictly outputs the absolute path for a specific installed version."""
    meta = {"tlc2_version_string": "TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)"}
    (installed_v180 / "meta-tla2tools.json").write_text(json.dumps(meta))

    result = runner.invoke(app, ["tools", "path", "v1.8.0"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "tla2tools.jar" in lines[0]
    assert Path(lines[0]).is_absolute()
    assert "TLC2 Version" not in result.stdout


def test_tlc_path_version_without_metadata(mock_load_config, mock_cache, installed_v180, runner):
    """path <version> strictly outputs the absolute path when no metadata exists."""
    result = runner.invoke(app, ["tools", "path", "v1.8.0"])
    assert result.exit_code == 0
    lines = result.stdout.strip().splitlines()
    assert len(lines) == 1
    assert "tla2tools.jar" in lines[0]
    assert Path(lines[0]).is_absolute()


def test_tlc_path_not_found(mock_load_config, mock_cache, runner):
    (mock_cache / "tlc").mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tools", "path", "v9.9.9"])
    assert result.exit_code == 1


def test_tlc_path_no_pinned(mock_load_config, mock_cache, runner):
    """path without args fails if nothing is pinned."""
    (mock_cache / "tlc").mkdir(parents=True, exist_ok=True)
    result = runner.invoke(app, ["tools", "path"])
    assert result.exit_code == 1
    assert "No pinned version" in result.output


def test_tlc_path_jar_missing(mock_load_config, mock_cache, runner):
    """path fails if pinned directory exists but tla2tools.jar is missing."""
    tools_dir = mock_cache / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    version_dir = tools_dir / "v1.8.0-aaaaaaa"
    version_dir.mkdir()
    # No jar file

    (tools_dir / "tools-pinned-version.txt").write_text("v1.8.0-aaaaaaa")

    result = runner.invoke(app, ["tools", "path"])
    assert result.exit_code == 1
    assert "No pinned version found." in result.output
