import contextlib
import hashlib
import shutil
from pathlib import Path

from tlaplus_cli.versioning.paths import get_tlc_run_dir


def compute_spec_hash(spec_file: Path) -> str:
    """Compute an 8-character SHA-256 short hash for a TLA+ specification and its configuration file."""
    hasher = hashlib.sha256()

    # Include absolute path string
    hasher.update(str(spec_file.absolute()).encode("utf-8"))

    # Include spec file contents if it exists
    with contextlib.suppress(OSError):
        hasher.update(spec_file.read_bytes())

    # Include .cfg file contents if present
    cfg_file = spec_file.with_suffix(".cfg")
    if cfg_file.is_file():
        with contextlib.suppress(OSError):
            hasher.update(cfg_file.read_bytes())

    return hasher.hexdigest()[:8]


def _cleanup_stale_spec_dirs(tlc_run_dir: Path, spec_stem: str, current_hash: str) -> None:
    """Remove older cached run directories for the spec stem that do not match the current hash."""
    if not tlc_run_dir.is_dir():
        return

    prefix = f"{spec_stem}_"
    current_dir_name = f"{spec_stem}_{current_hash}"

    for item in tlc_run_dir.iterdir():
        if item.is_dir() and item.name.startswith(prefix) and item.name != current_dir_name:
            with contextlib.suppress(OSError):
                shutil.rmtree(item)


def get_spec_run_dir(spec_file: Path) -> Path:
    """Get or create the isolated run directory for a spec and purge stale runs for the same spec."""
    spec_file = spec_file.absolute()
    short_hash = compute_spec_hash(spec_file)
    tlc_run_dir = get_tlc_run_dir()

    _cleanup_stale_spec_dirs(tlc_run_dir, spec_file.stem, short_hash)

    target_dir = tlc_run_dir / f"{spec_file.stem}_{short_hash}"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir


def clear_tlc_run_cache() -> None:
    """Purge all cached TLC run state directories."""
    tlc_run_dir = get_tlc_run_dir()
    if tlc_run_dir.exists():
        with contextlib.suppress(OSError):
            shutil.rmtree(tlc_run_dir)
