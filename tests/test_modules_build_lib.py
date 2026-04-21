from tlaplus_cli.cli import app
from tlaplus_cli.config import loader as config


def test_build_classpath_with_custom_lib(mocker, tmp_path, runner):
    """Test that build command uses custom module_lib_path in classpath."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)
    mocker.patch("tlaplus_cli.tlc.compiler.workspace_root", return_value=tmp_path)

    # Mock subprocess.run to avoid actual compilation
    mock_run = mocker.patch("subprocess.run")

    # Setup mock environment
    module_dir = tmp_path / "modules"
    module_dir.mkdir()
    (module_dir / "Test.java").write_text("public class Test {}")

    lib_dir = tmp_path / "custom_lib"
    lib_dir.mkdir()
    jar1 = lib_dir / "one.jar"
    jar1.touch()

    cfg = config.load_config()
    cfg.module_path = str(module_dir)
    cfg.module_lib_path = str(lib_dir)
    config.save_config(cfg)

    # Mock tla2tools.jar existence
    mocker.patch("tlaplus_cli.tlc.compiler.get_pinned_version_dir", return_value=None)
    mocker.patch("tlaplus_cli.tlc.compiler.cache_dir", return_value=tmp_path / "cache")
    (tmp_path / "cache").mkdir()
    tla2tools = tmp_path / "cache" / "tla2tools.jar"
    tla2tools.touch()

    result = runner.invoke(app, ["modules", "build"])
    assert result.exit_code == 0

    # Verify javac command
    args, _kwargs = mock_run.call_args
    cmd = args[0]
    cp_index = cmd.index("-cp")
    classpath = cmd[cp_index + 1]

    assert str(jar1) in classpath
    assert str(tla2tools) in classpath

def test_build_classpath_fallback_lib(mocker, tmp_path, runner):
    """Test that build command uses fallback lib (inside modules_dir) when not configured."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)
    mocker.patch("tlaplus_cli.tlc.compiler.workspace_root", return_value=tmp_path)

    mock_run = mocker.patch("subprocess.run")

    module_dir = tmp_path / "modules"
    module_dir.mkdir()
    (module_dir / "Test.java").write_text("public class Test {}")

    # Default lib location: modules_dir / lib
    lib_dir = module_dir / "lib"
    lib_dir.mkdir()
    jar2 = lib_dir / "two.jar"
    jar2.touch()

    cfg = config.load_config()
    cfg.module_path = str(module_dir)
    cfg.module_lib_path = None
    config.save_config(cfg)

    mocker.patch("tlaplus_cli.tlc.compiler.get_pinned_version_dir", return_value=None)
    mocker.patch("tlaplus_cli.tlc.compiler.cache_dir", return_value=tmp_path / "cache")
    (tmp_path / "cache").mkdir()
    tla2tools = tmp_path / "cache" / "tla2tools.jar"
    tla2tools.touch()

    result = runner.invoke(app, ["modules", "build"])
    assert result.exit_code == 0

    args, _kwargs = mock_run.call_args
    cmd = args[0]
    cp_index = cmd.index("-cp")
    classpath = cmd[cp_index + 1]

    assert str(jar2) in classpath
