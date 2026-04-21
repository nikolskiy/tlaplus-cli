import pytest


@pytest.fixture
def queue_dir(fixtures_dir):
    return fixtures_dir / "queue"


@pytest.fixture
def setup_naming_env_fixture(mocker):
    """Fixture providing the setup_naming_env helper."""

    def _setup(tmp_path, mocker_local, base_settings, fixture_dir):
        """Configures environment for naming tests."""
        classes_dir = tmp_path / "classes"
        classes_dir.mkdir()

        settings = base_settings.model_copy(deep=True)
        settings.workspace.root = fixture_dir
        settings.workspace.modules_dir = "modules"
        settings.workspace.spec_dir = "spec"
        settings.workspace.classes_dir = str(classes_dir)

        mocker_local.patch("tlaplus_cli.tlc.compiler.load_config", return_value=settings)
        mocker_local.patch("tlaplus_cli.tlc.compiler.workspace_root", return_value=fixture_dir)
        mocker_local.patch("tlaplus_cli.tlc.runner.load_config", return_value=settings)

    return _setup
