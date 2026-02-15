import shutil
from functools import lru_cache
from pathlib import Path

import platformdirs
import yaml

from tla.settings import Settings

_APP_NAME = "tla"


@lru_cache(maxsize=1)
def load_config() -> Settings:
    """Load config from the user config directory.

    Creates a default config on first run.
    """
    cp = _ensure_config()
    with cp.open() as f:
        data = yaml.safe_load(f)
        return Settings.model_validate(data)


def config_dir() -> Path:
    """OS-standard user config directory for this app."""
    return Path(platformdirs.user_config_dir(_APP_NAME))


def config_path() -> Path:
    """Path to the user's config.yaml."""
    return config_dir() / "config.yaml"


def cache_dir() -> Path:
    """OS-standard cache directory (stores tla2tools.jar)."""
    return Path(platformdirs.user_cache_dir(_APP_NAME))


def _default_config_path() -> Path:
    """Path to the default config shipped with the package."""
    return Path(__file__).parent / "resources" / "default_config.yaml"


def _ensure_config() -> Path:
    """Copy default config to user config dir if it doesn't exist yet."""
    cp = config_path()
    if not cp.exists():
        cp.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_default_config_path(), cp)
    return cp


def workspace_root() -> Path:
    """Return the resolved workspace root directory.

    Relative paths are resolved from the current working directory.
    """
    config = load_config()
    ws_root = Path(config.workspace.root)
    if not ws_root.is_absolute():
        ws_root = (Path.cwd() / ws_root).resolve()
    return ws_root
