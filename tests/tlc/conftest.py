import pytest


@pytest.fixture
def setup_naming_env_fixture(mocker):
    """Fixture providing the setup_naming_env helper."""

    def _setup(tmp_path, mocker_local, base_settings, fixture_dir):
        """Configures the mocks and settings for testing Java overrides from a fixture dir."""
        settings = base_settings.model_copy(deep=True)
        classes_dir = tmp_path / "classes"
        classes_dir.mkdir(parents=True, exist_ok=True)

        settings.workspace.root = fixture_dir
        settings.workspace.modules_dir = "modules"
        settings.workspace.spec_dir = "spec"
        settings.workspace.classes_dir = str(classes_dir)

        mocker_local.patch("tlaplus_cli.build_tlc_module.load_config", return_value=settings)
        mocker_local.patch("tlaplus_cli.build_tlc_module.workspace_root", return_value=fixture_dir)
        mocker_local.patch("tlaplus_cli.run_tlc.load_config", return_value=settings)

    return _setup
