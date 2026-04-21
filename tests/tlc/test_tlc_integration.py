import pytest

from tlaplus_cli.cli import app


def test_tlc_integration(
    mocker, tmp_path, capfd, queue_dir, base_settings, monkeypatch, runner, java_available, javac_available
):
    """
    Integration test for run_tlc.tlc().
    1. Compiles the modules (prerequisite).
    2. Runs TLC on queue.tla.
    3. Verifies output.
    """
    if not java_available:
        pytest.skip("java not found")
    if not javac_available:
        pytest.skip("javac not found")

    classes_dir = tmp_path / "classes"

    # Configure base_settings
    base_settings.workspace.root = queue_dir
    base_settings.workspace.classes_dir = classes_dir

    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=base_settings)

    # We also need to patch build_tlc_module's config loading to compile first
    mocker.patch("tlaplus_cli.tlc.compiler.load_config", return_value=base_settings)
    # Patch workspace_root for build_tlc_module
    mocker.patch("tlaplus_cli.tlc.compiler.workspace_root", return_value=queue_dir)

    # 1. Compile modules
    res_build = runner.invoke(app, ["modules", "build"])
    assert res_build.exit_code == 0, f"Module compilation failed: {res_build.stdout}"
    # 2. Run TLC
    # Verify that classes_dir is populated
    assert (classes_dir / "tlc2/overrides/TLCOverrides.class").exists()

    # Run TLC on "queue" spec
    monkeypatch.chdir(queue_dir)
    res_tlc = runner.invoke(app, ["tlc", "queue"])
    assert res_tlc.exit_code == 0, f"TLC run failed: {res_tlc.stdout}"

    # 3. Verify output
    captured = capfd.readouterr()
    stdout = captured.out + res_tlc.stdout

    assert "Running TLC on queue.tla" in stdout
    # The output might vary but we expect some successes
    assert "State log test:" in stdout
