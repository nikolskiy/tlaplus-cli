"""Project root discovery utilities."""

from pathlib import Path


def _is_project_root(directory: Path, modules_dir: Path | str, classes_dir: Path | str, lib_dir: Path | str) -> bool:
    """Return True if directory contains at least one project structure marker."""
    return (
        (directory / classes_dir).is_dir()
        or (directory / modules_dir).is_dir()
        or (directory / lib_dir).is_dir()
    )


def find_project_root(
    spec_file: Path,
    *,
    modules_dir: Path | str,
    classes_dir: Path | str,
    lib_dir: Path | str = "lib",
) -> Path | None:
    """Resolve the project root relative to a .tla spec file.

    Resolution strategy (in order):
    1. Check the spec file's own directory.
    2. Check the parent of the spec file's directory (handles spec/ and tests/ subdirs).
    3. Return None if neither directory qualifies.
    """
    spec_dir = spec_file.parent.resolve()

    for candidate in (spec_dir, spec_dir.parent):
        if _is_project_root(candidate, modules_dir, classes_dir, lib_dir):
            return candidate

    return None
