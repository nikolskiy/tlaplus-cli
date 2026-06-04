import json
import subprocess

from tlaplus_cli.cli import app
from tlaplus_cli.config import loader as config


def test_modules_add_success(mocker, tmp_path, runner):
    """Test that 'tla modules add' compiles Java files and copies dependencies to the cache."""
    # Setup directories
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    modules_cache_dir = tmp_path / "modules"
    modules_cache_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch("tlaplus_cli.cmd.modules.add.get_modules_dir", return_value=modules_cache_dir)
    mocker.patch("tlaplus_cli.java.classpath.get_modules_dir", return_value=modules_cache_dir)

    # Mock tool jar
    tla2tools = tmp_path / "tla2tools.jar"
    tla2tools.touch()
    mocker.patch("tlaplus_cli.tlc.compiler.get_tlc_jar_path", return_value=tla2tools)

    # Mock compiler subprocess.run to avoid actual execution but let it pretend success
    mocker.patch("subprocess.run")

    # Create dummy source project
    source_dir = tmp_path / "my-test-module"
    source_dir.mkdir()

    overrides_dir = source_dir / "tlc2" / "overrides"
    overrides_dir.mkdir(parents=True)
    (overrides_dir / "TestOverride.java").touch()

    lib_dir = source_dir / "lib"
    lib_dir.mkdir()
    (lib_dir / "dep.jar").touch()

    tla_dir = source_dir / "modules"
    tla_dir.mkdir()
    (tla_dir / "Test.tla").touch()

    test_dir = source_dir / "test"
    test_dir.mkdir()
    (test_dir / "Test_tests.tla").touch()

    # Invoke add command
    result = runner.invoke(app, ["modules", "add", str(source_dir)])

    assert result.exit_code == 0
    assert "Module 'my-test-module' successfully added" in result.output

    # Check that cache target exists
    target_cache_dir = modules_cache_dir / "my-test-module"
    assert target_cache_dir.exists()

    # Check classes directory compilation target was created
    assert (target_cache_dir / "classes").exists()
    assert (target_cache_dir / "classes" / "META-INF" / "services" / "tlc2.overrides.ITLCOverrides").exists()

    # Check lib files were copied
    assert (target_cache_dir / "lib" / "dep.jar").exists()

    # Check modules files were copied
    assert (target_cache_dir / "modules" / "Test.tla").exists()

    # Check tlc2 files were copied
    assert (target_cache_dir / "tlc2" / "overrides" / "TestOverride.java").exists()

    # Check test files were copied
    assert (target_cache_dir / "test" / "Test_tests.tla").exists()

    # Check metadata.json exists and is valid
    metadata_file = target_cache_dir / "metadata.json"
    assert metadata_file.exists()
    meta = json.loads(metadata_file.read_text())
    assert meta["name"] == "my-test-module"
    assert "built_at" in meta


def test_modules_add_compilation_failure(mocker, tmp_path, runner):
    """Test that 'tla modules add' removes the cached directory if compilation fails."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    modules_cache_dir = tmp_path / "modules"
    modules_cache_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch("tlaplus_cli.cmd.modules.add.get_modules_dir", return_value=modules_cache_dir)

    # Mock tool jar
    tla2tools = tmp_path / "tla2tools.jar"
    tla2tools.touch()
    mocker.patch("tlaplus_cli.tlc.compiler.get_tlc_jar_path", return_value=tla2tools)

    # Mock compiler to throw CalledProcessError
    err = subprocess.CalledProcessError(
        1,
        "javac",
        output="Compilation error output",
        stderr="Compilation stderr",
    )
    mocker.patch("subprocess.run", side_effect=err)

    # Create dummy source project with java overrides
    source_dir = tmp_path / "fail-module"
    source_dir.mkdir()
    overrides_dir = source_dir / "tlc2" / "overrides"
    overrides_dir.mkdir(parents=True)
    (overrides_dir / "Fail.java").touch()

    # Invoke add command
    result = runner.invoke(app, ["modules", "add", str(source_dir)])

    assert result.exit_code == 1
    assert "Compilation failed!" in result.output

    # Check that cache target does NOT exist (should have been deleted)
    target_cache_dir = modules_cache_dir / "fail-module"
    assert not target_cache_dir.exists()



def test_modules_list(mocker, tmp_path, runner):
    """Test that 'tla modules list' outputs a clean table of cached modules."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    modules_cache_dir = tmp_path / "modules"
    modules_cache_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch("tlaplus_cli.cmd.modules.list.get_modules_dir", return_value=modules_cache_dir)

    # Pre-populate two cached modules
    mod_a = modules_cache_dir / "mod-a"
    mod_a.mkdir()
    (mod_a / "metadata.json").write_text(json.dumps({"name": "mod-a", "built_at": "2026-06-04 12:00:00"}))

    mod_b = modules_cache_dir / "mod-b"
    mod_b.mkdir()
    (mod_b / "metadata.json").write_text(json.dumps({"name": "mod-b", "built_at": "2026-06-04 13:30:00"}))

    result = runner.invoke(app, ["modules", "list"])
    assert result.exit_code == 0
    assert "mod-a" in result.output
    assert "mod-b" in result.output
    assert "2026-06-04 12:00:00" in result.output
    assert "2026-06-04 13:30:00" in result.output


def test_modules_remove(mocker, tmp_path, runner):
    """Test that 'tla modules remove' deletes the module directory from cache."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    modules_cache_dir = tmp_path / "modules"
    modules_cache_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch("tlaplus_cli.cmd.modules.remove.get_modules_dir", return_value=modules_cache_dir)

    # Pre-populate module
    mod = modules_cache_dir / "to-remove"
    mod.mkdir()
    (mod / "metadata.json").write_text(json.dumps({"name": "to-remove"}))

    assert mod.exists()

    result = runner.invoke(app, ["modules", "remove", "to-remove"])
    assert result.exit_code == 0
    assert "Module 'to-remove' successfully deleted" in result.output
    assert not mod.exists()


def test_modules_remove_nonexistent(mocker, tmp_path, runner):
    """Test removing a nonexistent module shows error."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    modules_cache_dir = tmp_path / "modules"
    modules_cache_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch("tlaplus_cli.cmd.modules.remove.get_modules_dir", return_value=modules_cache_dir)

    result = runner.invoke(app, ["modules", "remove", "missing"])
    assert result.exit_code == 1
    assert "Module 'missing' not found" in result.output


def test_modules_path_view(mocker, tmp_path, runner):
    """Test that 'tla modules path' displays resolved paths for cached modules."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    modules_cache_dir = tmp_path / "modules"
    modules_cache_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch("tlaplus_cli.cmd.modules.path.get_modules_dir", return_value=modules_cache_dir)
    mocker.patch("tlaplus_cli.java.classpath.get_modules_dir", return_value=modules_cache_dir)

    # Set up tools jar
    tla2tools = tmp_path / "tla2tools.jar"
    tla2tools.touch()
    mocker.patch("tlaplus_cli.cmd.modules.path.get_tlc_jar_path", return_value=tla2tools)

    # Pre-populate a module
    mod = modules_cache_dir / "my-cached-mod"
    mod.mkdir()
    (mod / "classes").mkdir()
    (mod / "lib").mkdir()
    (mod / "lib" / "nested.jar").touch()
    (mod / "modules").mkdir()

    result = runner.invoke(app, ["modules", "path"])
    assert result.exit_code == 0
    assert "Source Paths" in result.output
    assert "Classes Paths" in result.output
    assert "Library Paths" in result.output
    assert str(mod / "classes") in result.output
    assert str(mod / "lib" / "nested.jar") in result.output
    assert str(mod / "modules") in result.output


def test_modules_path_empty_no_project_leaks(mocker, tmp_path, runner):
    """Test that 'tla modules path' displays 'None' when cache is empty, ignoring project-local folders."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    modules_cache_dir = tmp_path / "modules"
    modules_cache_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch("tlaplus_cli.cmd.modules.path.get_modules_dir", return_value=modules_cache_dir)
    mocker.patch("tlaplus_cli.java.classpath.get_modules_dir", return_value=modules_cache_dir)

    # Set up tools jar
    tla2tools = tmp_path / "tla2tools.jar"
    tla2tools.touch()
    mocker.patch("tlaplus_cli.cmd.modules.path.get_tlc_jar_path", return_value=tla2tools)

    # Mock a project-local classes folder in the current workspace (simulate repo root classes/)
    (tmp_path / "classes").mkdir()

    result = runner.invoke(app, ["modules", "path"])
    assert result.exit_code == 0
    assert "Source Paths (-DTLA-Library):\n  None" in result.output
    assert "Classes Paths:\n  None" in result.output
    assert "Library Paths (JARs):\n  None" in result.output


def test_modules_add_nested_overrides(mocker, tmp_path, runner):
    """Test that 'tla modules add' successfully compiles Java files nested under modules/tlc2/overrides."""
    config.load_config.cache_clear()
    config_dir = tmp_path / "config"
    mocker.patch("tlaplus_cli.config.loader.config_dir", return_value=config_dir)

    modules_cache_dir = tmp_path / "modules"
    modules_cache_dir.mkdir(parents=True, exist_ok=True)
    mocker.patch("tlaplus_cli.cmd.modules.add.get_modules_dir", return_value=modules_cache_dir)

    # Mock tool jar
    tla2tools = tmp_path / "tla2tools.jar"
    tla2tools.touch()
    mocker.patch("tlaplus_cli.tlc.compiler.get_tlc_jar_path", return_value=tla2tools)

    # Mock compiler subprocess.run
    mocker.patch("subprocess.run")

    # Create dummy source project with nested overrides
    source_dir = tmp_path / "nested-module"
    source_dir.mkdir()

    # Nested overrides structure: modules/tlc2/overrides/
    nested_overrides = source_dir / "modules" / "tlc2" / "overrides"
    nested_overrides.mkdir(parents=True)
    (nested_overrides / "MyNestedOverride.java").touch()

    result = runner.invoke(app, ["modules", "add", str(source_dir)])
    assert result.exit_code == 0
    assert "Module 'nested-module' successfully added" in result.output

    # Check that classes directory and service file exist in the cache
    target_cache_dir = modules_cache_dir / "nested-module"
    assert (target_cache_dir / "classes").exists()
    assert (target_cache_dir / "classes" / "META-INF" / "services" / "tlc2.overrides.ITLCOverrides").exists()
    assert (target_cache_dir / "modules" / "tlc2" / "overrides" / "MyNestedOverride.java").exists()

