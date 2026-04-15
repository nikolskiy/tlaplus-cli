import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tlaplus_cli.settings import Settings

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests/fixtures"


@pytest.fixture(scope="session")
def runner() -> CliRunner:
    """Session-scoped CLI runner."""
    return CliRunner()


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Root directory of the project."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Path to the fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture(scope="session")
def queue_dir() -> Path:
    """Path to the queue example fixture."""
    return FIXTURES_DIR / "queue"


@pytest.fixture
def javac_available() -> bool:
    """Check if javac is available on the system."""
    return shutil.which("javac") is not None


@pytest.fixture
def java_available() -> bool:
    """Check if java is available on the system."""
    return shutil.which("java") is not None


@pytest.fixture
def base_settings(tmp_path: Path) -> Settings:
    """
    Returns a basic valid Settings object with workspace paths pointing to tmp_path.
    Can be modified by tests before patching.
    """
    return Settings(
        tla={
            "urls": {
                "tags": "https://api.github.com/repos/tlaplus/tlaplus/tags",
                "releases": "https://api.github.com/repos/tlaplus/tlaplus/releases",
            }
        },
        tlc={"java_class": "tlc2.TLC"},
        # check_env_opts validator might run, simpler to provide explicit opts if needed,
        # or rely on default empty list if env var not set.
        java={"min_version": 11, "opts": []},
        workspace={
            "root": str(tmp_path),
            "modules_dir": "modules",
            "spec_dir": "spec",
            "classes_dir": "classes",
        },
    )


@pytest.fixture
def mock_load_config(mocker, base_settings):
    """
    Patches tlaplus_cli.config.load_config to return base_settings.
    Also patches consumers in specific modules if they import it directly.
    """
    return mocker.patch("tlaplus_cli.config.load_config", return_value=base_settings)


@pytest.fixture
def mock_cache(mocker, tmp_path):
    """Point cache_dir to a temporary directory."""
    mocker.patch("tlaplus_cli.config.cache_dir", return_value=tmp_path)
    # Patch modules that might have already imported cache_dir
    mocker.patch("tlaplus_cli.version_manager.cache_dir", return_value=tmp_path)
    mocker.patch("tlaplus_cli.tools_manager.cache_dir", return_value=tmp_path)
    mocker.patch("tlaplus_cli.run_tlc.cache_dir", return_value=tmp_path)
    mocker.patch("tlaplus_cli.build_tlc_module.cache_dir", return_value=tmp_path)
    return tmp_path


@pytest.fixture
def make_installed_version(mock_cache):
    """Factory fixture to create pre-installed versions."""

    def _make(name, sha, *, meta=None):
        tools_dir = mock_cache / "tools"
        tools_dir.mkdir(parents=True, exist_ok=True)
        version_dir = tools_dir / f"{name}-{sha}"
        version_dir.mkdir(exist_ok=True)
        (version_dir / "tla2tools.jar").write_bytes(b"fake jar content")
        if meta:
            (version_dir / "meta-tla2tools.json").write_text(json.dumps(meta))
        return version_dir

    return _make
