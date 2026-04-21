import json
from dataclasses import asdict
from pathlib import Path

from tlaplus_cli.ui import warn
from tlaplus_cli.versioning.schema import RemoteVersion


def load_github_cache(cache_file: Path) -> list[RemoteVersion] | None:
    """Load the remote versions cache from disk."""
    if cache_file.exists():
        try:
            with cache_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return [RemoteVersion(**item) for item in data]
        except (json.JSONDecodeError, OSError, KeyError, TypeError) as e:
            warn(f"Failed to read cache: {e}")
    return None


def save_github_cache(cache_file: Path, versions: list[RemoteVersion]) -> None:
    """Save the remote versions cache to disk."""
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with cache_file.open("w", encoding="utf-8") as f:
            json.dump([asdict(v) for v in versions], f)
    except OSError as e:
        warn(f"Failed to save cache: {e}")
