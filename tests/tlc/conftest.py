import os
import subprocess

import pytest

from tlaplus_cli.java.classpath import ClasspathResolver, ResolveMode
from tlaplus_cli.tlc.compiler import get_tlc_jar_path


@pytest.fixture
def queue_dir(fixtures_dir):
    return fixtures_dir / "queue"


@pytest.fixture
def setup_naming_env_fixture(mocker):
    """Fixture providing the setup_naming_env helper."""

    def _setup(tmp_path, mocker_local, base_settings, fixture_dir):
        """Configures environment for naming tests."""
        classes_dir = tmp_path / "classes"
        classes_dir.mkdir(exist_ok=True)

        settings = base_settings.model_copy(deep=True)
        settings.workspace.root = fixture_dir
        settings.workspace.modules_dir = "modules"
        settings.workspace.spec_dir = "spec"
        settings.workspace.classes_dir = str(classes_dir)

        mocker_local.patch("tlaplus_cli.tlc.runner.load_config", return_value=settings)

    return _setup


@pytest.fixture
def compile_test_modules_fixture():
    """Fixture to manually compile Java modules for tests without using 'modules build' command."""

    def _compile(fixture_dir, classes_dir, settings):
        classes_dir.mkdir(parents=True, exist_ok=True)
        # Find java files
        java_files = list((fixture_dir / "modules" / "tlc2" / "overrides").rglob("*.java"))
        if not java_files:
            java_files = list((fixture_dir / "tlc2" / "overrides").rglob("*.java"))

        tool_jar = get_tlc_jar_path()
        resolver = ClasspathResolver(settings, project_root=fixture_dir, tool_jar=tool_jar)
        classpath = os.pathsep.join(resolver.resolve(ResolveMode.COMPILE))

        cmd = ["javac", "-cp", classpath, "-d", str(classes_dir), *[str(f) for f in java_files]]
        subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Write service file
        meta_inf = classes_dir / "META-INF" / "services"
        meta_inf.mkdir(parents=True, exist_ok=True)
        service_file = meta_inf / "tlc2.overrides.ITLCOverrides"
        with service_file.open("w") as f:
            f.write(f"{settings.tlc.overrides_class}\n")

    return _compile
