import json
import shutil
from pathlib import Path

import pytest

from tlaplus_cli.cli import app
from tlaplus_cli.cmd.tlc import TlcFormatter
from tlaplus_cli.tlc.models import CheckState


def find_real_tla2tools_jar() -> Path | None:
    real_tools_dir = Path.home() / ".cache" / "tla" / "tools"
    if real_tools_dir.is_dir():
        for jar_path in real_tools_dir.glob("**/tla2tools.jar"):
            if jar_path.exists():
                return jar_path
    return None


def test_community_modules_integration(
    mocker,
    tmp_path,
    runner,
    java_available,
    javac_available,
    base_settings,
    monkeypatch,
    fixtures_dir,
    mock_cache,  # This overrides the cache dir to tmp_path
):
    """
    Integration test for CommunityModules and SequencesExt.
    1. Locates the real tla2tools.jar from user's cache and copies it to mock cache tools dir.
    2. Runs 'tla modules add' on the local CommunityModules repository.
    3. Runs TLC on the SequencesExtTest fixture.
    4. Verifies that Java overrides are loaded successfully and the spec succeeds.
    """
    if not java_available:
        pytest.skip("java not found")
    if not javac_available:
        pytest.skip("javac not found")

    real_jar = find_real_tla2tools_jar()
    if not real_jar or not real_jar.exists():
        pytest.skip("real tla2tools.jar not found in cache")

    # 1. Setup mocked cache tools directory with real tla2tools.jar
    version_name = real_jar.parent.name  # e.g. "v1.8.0-8ba1027"
    tools_dir = mock_cache / "tools"
    version_dir = tools_dir / version_name
    version_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(real_jar, version_dir / "tla2tools.jar")

    # Write metadata so list/pin works
    meta = {
        "version": version_name.split("-")[0],
        "tag_commit": version_name.split("-")[1] if "-" in version_name else "",
        "download_url": "mock_url",
        "published_at": "2026-06-04 12:00:00",
    }
    (version_dir / "meta-tla2tools.json").write_text(json.dumps(meta))

    # Pin this version
    pin_file = tools_dir / "tools-pinned-version.txt"
    pin_file.write_text(version_name)

    # 2. Configure base_settings for workspace root
    proj_root = Path(__file__).parent.parent.parent
    spec_dir = proj_root / "docs" / "examples" / "spec"
    base_settings.workspace.root = str(proj_root / "docs" / "examples")
    mocker.patch("tlaplus_cli.tlc.runner.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.cmd.modules.add.load_config", return_value=base_settings)
    mocker.patch("tlaplus_cli.tlc.runner.validate_java_version")

    # 3. Add the sequences-ext module using 'modules add' command
    repo_seq_dir = proj_root / "docs" / "examples" / "sequences-ext"
    assert repo_seq_dir.is_dir(), f"sequences-ext repository not found at {repo_seq_dir}"

    res_add = runner.invoke(app, ["modules", "add", str(repo_seq_dir)])
    assert res_add.exit_code == 0, f"modules add failed: {res_add.output}"

    # Verify files compiled and ITLCOverrides service file created
    classes_dir = mock_cache / "modules" / "sequences-ext" / "classes"
    assert (classes_dir / "tlc2" / "overrides" / "TLCOverrides.class").exists()
    assert (classes_dir / "META-INF" / "services" / "tlc2.overrides.ITLCOverrides").exists()

    # 4. Run TLC on 'SequencesExtTest' spec
    monkeypatch.chdir(spec_dir)

    captured_result = None
    original_update_logs = TlcFormatter.update_logs

    def mock_update_logs(self, layout, result):
        nonlocal captured_result
        captured_result = result
        original_update_logs(self, layout, result)

    mocker.patch("tlaplus_cli.cmd.tlc.TlcFormatter.update_logs", mock_update_logs)

    res_tlc = runner.invoke(app, ["tlc", "SequencesExtTest"])
    assert res_tlc.exit_code == 0, f"TLC run failed: {res_tlc.stdout}"

    # 5. Verify the logs and state
    assert captured_result is not None
    assert captured_result.state == CheckState.Success

    output_lines_str = "\n".join(captured_result.output_lines)
    assert "SUCCESS: Java overrides are loaded!" in output_lines_str
