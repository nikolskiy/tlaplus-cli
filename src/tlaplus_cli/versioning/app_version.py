"""App version discovery and git commit resolution for development installations."""

import importlib.metadata
import json
import subprocess
from pathlib import Path


def is_editable_install() -> bool:
    """Check if the tlaplus-cli package is installed in editable / development mode."""
    try:
        dist = importlib.metadata.distribution("tlaplus-cli")
        raw = dist.read_text("direct_url.json")
        if raw:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("dir_info", {}).get("editable") is True:
                return True

        origin = getattr(dist, "origin", None)
        if origin is not None:
            dir_info = getattr(origin, "dir_info", None)
            if dir_info is not None and getattr(dir_info, "editable", None) is True:
                return True
    except (importlib.metadata.PackageNotFoundError, json.JSONDecodeError, TypeError, KeyError, AttributeError):
        pass
    return False


def get_git_commit_hash(base_dir: Path | None = None) -> str | None:
    """Attempt to retrieve short git commit hash using git rev-parse --short HEAD."""
    cmd = ["git", "rev-parse", "--short", "HEAD"]
    cwd = base_dir if (base_dir and base_dir.is_dir()) else Path(__file__).parent
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=cwd)
        if res.returncode == 0:
            commit = res.stdout.strip()
            if commit and len(commit) >= 7:
                return commit
    except (subprocess.SubprocessError, OSError):
        pass
    return None


def get_app_version(base_version: str | None = None, base_dir: Path | None = None) -> str:
    """Return the application version string.

    Appends short git commit hash if running in an editable/development installation.
    """
    if not base_version:
        try:
            meta = importlib.metadata.metadata("tlaplus-cli")
            base_version = meta["Version"]
        except (importlib.metadata.PackageNotFoundError, KeyError):
            base_version = "0.0.0"

    git_hash = get_git_commit_hash(base_dir)
    repo_git = (Path(__file__).parent / "../../..").resolve() / ".git"
    is_dev = is_editable_install() or base_dir is not None or repo_git.exists()
    if git_hash and is_dev:
        return f"{base_version}+{git_hash}"

    return base_version
