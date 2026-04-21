import importlib.resources
from functools import lru_cache
from pathlib import Path

import platformdirs
import yaml

from tlaplus_cli.config.schema import Settings

_APP_NAME = "tla"


@lru_cache(maxsize=1)
def load_config() -> Settings:
    """Load config from the user config directory.

    Creates a default config on first run.
    """
    cp = _ensure_config()
    with cp.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return Settings.model_validate(data)


def save_config(settings: Settings) -> None:
    """Save config to the user config directory.

    Uses a defensive deep copy of settings.
    """
    cp = config_path()
    # defensive deep copy as per plan
    base_settings = settings.model_copy(deep=True)

    # Convert to dict, excluding None values for a cleaner config if desired,
    # but the plan doesn't specify exclusion. Pydantic's model_dump is good.
    data = base_settings.model_dump(mode="json")

    with cp.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False)

    # Clear cache to ensure subsequent loads get the new data
    load_config.cache_clear()


def config_dir() -> Path:
    """OS-standard user config directory for this app."""
    return Path(platformdirs.user_config_dir(_APP_NAME))


def config_path() -> Path:
    """Path to the user's config.yaml."""
    return config_dir() / "config.yaml"


def cache_dir() -> Path:
    """OS-standard cache directory (stores tla2tools.jar)."""
    return Path(platformdirs.user_cache_dir(_APP_NAME))


def _default_config_content() -> str:
    """Read the default config shipped with the package."""
    # Safer than __file__, correctly handles zipped wheels and zipapps.
    return (
        importlib.resources.files("tlaplus_cli.resources").joinpath("default_config.yaml").read_text(encoding="utf-8")
    )


def _ensure_config() -> Path:
    """Copy default config to user config dir if it doesn't exist yet."""
    cp = config_path()
    if not cp.exists():
        cp.parent.mkdir(parents=True, exist_ok=True)
        # Write default config to the newly created path
        cp.write_text(_default_config_content(), encoding="utf-8")
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
