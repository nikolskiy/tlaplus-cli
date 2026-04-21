from pathlib import Path

import typer

from tlaplus_cli.config.loader import cache_dir


def get_github_cache_file() -> Path:
    return cache_dir() / "github_cache.json"


def get_tools_dir() -> Path:
    return cache_dir() / "tools"


def get_pinned_path() -> Path:
    """Returns path to the pin marker file."""
    return get_tools_dir() / "tools-pinned-version.txt"


def get_pinned_version_dir() -> Path | None:
    """Returns the pinned version directory, or None if not pinned."""
    _migrate_legacy_pin()
    pin_file = get_pinned_path()
    if not pin_file.exists():
        return None
    dir_name = pin_file.read_text().strip()
    if not dir_name:
        return None
    target = get_tools_dir() / dir_name
    return target if target.is_dir() else None


def _migrate_legacy_pin() -> None:
    """Migrate legacy cache directory and pin files."""
    old_dir = cache_dir() / "tlc"
    new_dir = get_tools_dir()

    # 1. Migrate directory
    if old_dir.exists() and not new_dir.exists():
        try:
            old_dir.rename(new_dir)
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to migrate legacy cache: {e}", err=True)

    # 2. Migrate legacy symlink pin
    legacy_symlink = new_dir / "pinned"
    if legacy_symlink.is_symlink():
        try:
            target_name = legacy_symlink.readlink().name
            legacy_symlink.unlink()
            get_pinned_path().write_text(target_name)
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to migrate legacy symlink pin: {e}", err=True)

    # 3. Migrate legacy filename tlc-pinned-version.txt -> tools-pinned-version.txt
    old_pin_file = new_dir / "tlc-pinned-version.txt"
    new_pin_file = get_pinned_path()
    if old_pin_file.exists() and not new_pin_file.exists():
        try:
            old_pin_file.rename(new_pin_file)
        except Exception as e:
            typer.echo(f"⚠ Warning: Failed to migrate legacy pin file: {e}", err=True)


def set_pin(version_dir: Path) -> None:
    """Pin a version by writing its directory name to tools-pinned-version.txt."""
    pin_file = get_pinned_path()
    pin_file.parent.mkdir(parents=True, exist_ok=True)
    pin_file.write_text(version_dir.name)


def clear_pin() -> None:
    """Remove the pin."""
    pin_file = get_pinned_path()
    if pin_file.exists():
        pin_file.unlink()


def clear_cache() -> None:
    cache_file = get_github_cache_file()
    if cache_file.exists():
        cache_file.unlink()
