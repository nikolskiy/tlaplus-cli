from tlaplus_cli.version_manager import _migrate_legacy_pin, get_pinned_path, get_tools_dir


def test_migrate_legacy_dir(mock_cache):
    """If 'tlc' directory exists but 'tools' doesn't, rename it."""
    old_dir = mock_cache / "tlc"
    old_dir.mkdir()
    new_dir = get_tools_dir()
    assert not new_dir.exists()

    _migrate_legacy_pin()

    assert not old_dir.exists()
    assert new_dir.exists()


def test_migrate_legacy_symlink(mock_cache):
    """If 'pinned' is a symlink, convert it to a pin file."""
    tools_dir = get_tools_dir()
    tools_dir.mkdir(parents=True)

    version_dir = tools_dir / "v1.8.0-aaaaaaa"
    version_dir.mkdir()

    legacy_symlink = tools_dir / "pinned"
    legacy_symlink.symlink_to(version_dir.name)

    _migrate_legacy_pin()

    assert not legacy_symlink.exists()
    pin_file = get_pinned_path()
    assert pin_file.exists()
    assert pin_file.read_text().strip() == "v1.8.0-aaaaaaa"


def test_migrate_legacy_filename(mock_cache):
    """If 'tlc-pinned-version.txt' exists, rename it to 'tools-pinned-version.txt'."""
    tools_dir = get_tools_dir()
    tools_dir.mkdir(parents=True)

    old_pin = tools_dir / "tlc-pinned-version.txt"
    old_pin.write_text("v1.7.0-bbbbbbb")

    _migrate_legacy_pin()

    assert not old_pin.exists()
    new_pin = get_pinned_path()
    assert new_pin.exists()
    assert new_pin.read_text().strip() == "v1.7.0-bbbbbbb"
