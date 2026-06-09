from pathlib import Path

from tlaplus_cli.config.loader import cache_dir
from tlaplus_cli.versioning import get_pinned_version_dir


def get_tlc_jar_path() -> Path:
    """Resolve the path to tla2tools.jar using the fallback chain: pinned -> legacy."""
    pinned_dir = get_pinned_version_dir()
    pinned_jar = pinned_dir / "tla2tools.jar" if pinned_dir else None
    legacy = cache_dir() / "tla2tools.jar"
    return pinned_jar if (pinned_jar and pinned_jar.exists()) else legacy
