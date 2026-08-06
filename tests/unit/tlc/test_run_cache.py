from pathlib import Path
from typing import Any

from tlaplus_cli.tlc.run_cache import (
    clear_tlc_run_cache,
    compute_spec_hash,
    get_spec_run_dir,
)


def test_compute_spec_hash(tmp_path: Path) -> None:
    spec_file = tmp_path / "MySpec.tla"
    spec_file.write_text("---- MODULE MySpec ----\n====\n")

    hash1 = compute_spec_hash(spec_file)
    assert len(hash1) == 8

    # Modify spec file -> hash should change
    spec_file.write_text("---- MODULE MySpec ----\nVARIABLES x\n====\n")
    hash2 = compute_spec_hash(spec_file)
    assert hash1 != hash2

    # Add .cfg file -> hash should change
    cfg_file = tmp_path / "MySpec.cfg"
    cfg_file.write_text("SPECIFICATION Spec\n")
    hash3 = compute_spec_hash(spec_file)
    assert hash2 != hash3


def test_get_spec_run_dir_and_stale_cleanup(tmp_path: Path, mocker: Any) -> None:
    tlc_run_dir = tmp_path / "cache" / "run" / "tlc"
    mocker.patch("tlaplus_cli.tlc.run_cache.get_tlc_run_dir", return_value=tlc_run_dir)

    spec_file = tmp_path / "Spec.tla"
    spec_file.write_text("MODULE Spec")

    # Pre-create a stale run directory for the same spec stem
    stale_dir = tlc_run_dir / "Spec_12345678"
    stale_dir.mkdir(parents=True, exist_ok=True)
    (stale_dir / "state.txt").write_text("stale state")

    run_dir = get_spec_run_dir(spec_file)

    assert run_dir.exists()
    assert run_dir.parent == tlc_run_dir
    assert not stale_dir.exists()


def test_clear_tlc_run_cache(tmp_path: Path, mocker: Any) -> None:
    tlc_run_dir = tmp_path / "cache" / "run" / "tlc"
    mocker.patch("tlaplus_cli.tlc.run_cache.get_tlc_run_dir", return_value=tlc_run_dir)

    run_dir = tlc_run_dir / "Spec_11223344"
    run_dir.mkdir(parents=True, exist_ok=True)
    assert tlc_run_dir.exists()

    clear_tlc_run_cache()
    assert not tlc_run_dir.exists()
