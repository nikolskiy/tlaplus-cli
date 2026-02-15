import shutil
from pathlib import Path

import pytest

from tla.settings import Settings

PROJECT_ROOT = Path(__file__).parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests/fixtures"


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Root directory of the project."""
    return PROJECT_ROOT


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
        tla={"jar_name": "tla2tools.jar", "urls": {"stable": "http://stable.url", "nightly": "http://nightly.url"}},
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
    Patches tla.config.load_config to return base_settings.
    Also patches consumers in specific modules if they import it directly.
    """
    return mocker.patch("tla.config.load_config", return_value=base_settings)
