import importlib.metadata

from tlaplus_cli.versioning.app_version import (
    get_app_version,
    get_git_commit_hash,
    is_editable_install,
)


def test_get_git_commit_hash_success(mocker, tmp_path):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "1234567\n"

    commit = get_git_commit_hash(tmp_path)
    assert commit == "1234567"
    mock_run.assert_called_once_with(
        ["git", "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )


def test_get_git_commit_hash_failure(mocker, tmp_path):
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value.returncode = 128
    mock_run.return_value.stdout = ""

    commit = get_git_commit_hash(tmp_path)
    assert commit is None


def test_get_git_commit_hash_exception(mocker, tmp_path):
    mocker.patch("subprocess.run", side_effect=OSError("git not found"))
    commit = get_git_commit_hash(tmp_path)
    assert commit is None


def test_is_editable_install_true(mocker):
    mock_dist = mocker.patch("importlib.metadata.distribution")
    mock_dist.return_value.read_text.return_value = '{"dir_info": {"editable": true}}'

    assert is_editable_install() is True


def test_is_editable_install_false(mocker):
    mock_dist = mocker.patch("importlib.metadata.distribution")
    mock_dist.return_value.read_text.return_value = '{"url": "file:///path"}'
    mock_dist.return_value.origin = None

    assert is_editable_install() is False


def test_is_editable_install_package_not_found(mocker):
    mocker.patch("importlib.metadata.distribution", side_effect=importlib.metadata.PackageNotFoundError)

    assert is_editable_install() is False


def test_get_app_version_editable(mocker, tmp_path):
    mocker.patch("tlaplus_cli.versioning.app_version.is_editable_install", return_value=True)
    mocker.patch("tlaplus_cli.versioning.app_version.get_git_commit_hash", return_value="abcdef1")
    mock_meta = mocker.patch("importlib.metadata.metadata")
    mock_meta.return_value = {"Version": "0.7.0"}

    version = get_app_version(base_dir=tmp_path)
    assert version == "0.7.0+abcdef1"


def test_get_app_version_release(mocker):
    mocker.patch("tlaplus_cli.versioning.app_version.is_editable_install", return_value=False)
    mocker.patch("tlaplus_cli.versioning.app_version.get_git_commit_hash", return_value=None)
    mock_meta = mocker.patch("importlib.metadata.metadata")
    mock_meta.return_value = {"Version": "0.7.0"}

    version = get_app_version()
    assert version == "0.7.0"
