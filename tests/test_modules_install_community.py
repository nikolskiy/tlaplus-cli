from unittest.mock import MagicMock

import pytest

from tlaplus_cli.cli import app
from tlaplus_cli.config.schema import TlaUrls
from tlaplus_cli.java.classpath import ClasspathResolver, ResolveMode

MOCK_MODULE_TAGS = [
    {
        "name": "v2024.12.17",
        "commit": {"sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
    },
]

MOCK_MODULE_RELEASES = [
    {
        "tag_name": "v2024.12.17",
        "assets": [
            {
                "name": "CommunityModules.jar",
                "browser_download_url": "https://example.com/CommunityModules.jar",
            }
        ],
    },
]


@pytest.fixture
def mock_community_api(mocker):
    """Mock GitHub API responses for CommunityModules."""
    mock_tags = MagicMock()
    mock_tags.json.return_value = MOCK_MODULE_TAGS
    mock_tags.raise_for_status = MagicMock()

    mock_releases = MagicMock()
    mock_releases.json.return_value = MOCK_MODULE_RELEASES
    mock_releases.raise_for_status = MagicMock()

    def side_effect(url, **kwargs):
        if "CommunityModules" in url:
            if "tags" in url:
                return mock_tags
            return mock_releases
        return MagicMock()

    mocker.patch("tlaplus_cli.versioning.api.requests.get", side_effect=side_effect)


@pytest.fixture
def mock_modules_settings(mocker, base_settings):
    """Ensure community_modules URLs are in settings."""
    base_settings.tla.community_modules = TlaUrls(
        tags="https://api.github.com/repos/tlaplus/CommunityModules/tags",
        releases="https://api.github.com/repos/tlaplus/CommunityModules/releases",
    )
    return mocker.patch("tlaplus_cli.cmd.modules.install.load_config", return_value=base_settings)


def test_install_community_modules(mock_community_api, mock_modules_settings, mock_cache, runner, mocker):
    # Mock download_version to avoid actual download
    mock_dl = mocker.patch("tlaplus_cli.cmd.modules.install.download_version")
    mock_dl.return_value = mock_cache / "modules" / "v2024.12.17-bbbbbbb"

    result = runner.invoke(app, ["modules", "install-community"])
    assert result.exit_code == 0
    output = result.stdout + result.stderr
    assert "Successfully installed v2024.12.17" in output

    # Verify it called fetch_remote_versions with correct asset name
    mock_dl.assert_called_once()
    assert mock_dl.call_args[1]["jar_name"] == "CommunityModules.jar"
    assert "modules" in str(mock_dl.call_args[1]["base_dir"])


def test_classpath_includes_managed_modules(mock_cache, base_settings):
    # Create a dummy managed module
    module_dir = mock_cache / "modules" / "test-module-1234567"
    module_dir.mkdir(parents=True)
    jar_file = module_dir / "CommunityModules.jar"
    jar_file.write_bytes(b"fake")

    resolver = ClasspathResolver(base_settings, project_root=None)
    cp = resolver.resolve(ResolveMode.RUNTIME)

    assert str(jar_file.absolute()) in cp
