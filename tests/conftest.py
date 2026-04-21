import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tlaplus_cli.config.schema import Settings

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests/fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def base_settings():
    """Returns a basic Settings object matching default_config.yaml."""
    return Settings(
        tla={
            "urls": {
                "tags": "https://api.github.com/repos/tlaplus/tlaplus/tags",
                "releases": "https://api.github.com/repos/tlaplus/tlaplus/releases",
            }
        },
        workspace={
            "root": ".",
            "spec_dir": "spec",
            "modules_dir": "modules",
            "classes_dir": "classes",
        },
        tlc={
            "java_class": "tlc2.TLC",
            "overrides_class": "tlc2.overrides.TLCOverrides",
        },
        java={"min_version": 11, "opts": []},
    )


@pytest.fixture
def mock_load_config(mocker, base_settings):
    """Mocks load_config to return base_settings and prevents writing to disk."""
    return mocker.patch("tlaplus_cli.config.loader.load_config", return_value=base_settings)


@pytest.fixture
def mock_cache(mocker, tmp_path):
    """Point cache_dir to a temporary directory."""
    mocker.patch("tlaplus_cli.config.loader.cache_dir", return_value=tmp_path)
    # Patch modules that might have already imported cache_dir
    mocker.patch("tlaplus_cli.versioning.paths.cache_dir", return_value=tmp_path, create=True)
    # tlc.compiler DOES import cache_dir
    mocker.patch("tlaplus_cli.tlc.compiler.cache_dir", return_value=tmp_path, create=True)
    # New command modules
    mocker.patch("tlaplus_cli.cmd.tools.uninstall.cache_dir", return_value=tmp_path, create=True)
    mocker.patch("tlaplus_cli.cmd.tools.install.cache_dir", return_value=tmp_path, create=True)
    return tmp_path


@pytest.fixture
def make_installed_version(mock_cache):
    """Factory fixture to create pre-installed versions."""

    def _make(name, sha, meta=None):
        tools_dir = (mock_cache / "tools").absolute()
        tools_dir.mkdir(parents=True, exist_ok=True)
        version_dir = tools_dir / f"{name}-{sha}"
        version_dir.mkdir(exist_ok=True)
        (version_dir / "tla2tools.jar").write_bytes(b"fake jar content")
        if meta:
            (version_dir / "meta-tla2tools.json").write_text(json.dumps(meta))
        return version_dir

    return _make


@pytest.fixture
def java_available(mocker):
    """Mock shutil.which to find 'java'."""
    return mocker.patch("shutil.which", side_effect=lambda x: "/usr/bin/java" if x == "java" else None)


@pytest.fixture
def javac_available(mocker):
    """Mock shutil.which to find 'javac'."""
    return mocker.patch("shutil.which", side_effect=lambda x: "/usr/bin/javac" if x == "javac" else None)
