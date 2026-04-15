import pytest

from tlaplus_cli.version_manager import extract_version_from_url, is_url


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://example.com/v1.8.0/tla2tools.jar", True),
        ("http://example.com/tla2tools.jar", True),
        ("v1.8.0", False),
        ("", False),
    ],
)
def test_is_url(url, expected):
    assert is_url(url) is expected


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://example.com/v1.8.0/tla2tools.jar", "v1.8.0"),
        ("https://example.com/custom/v1.8.0/build/tla2tools.jar", "v1.8.0"),
        ("https://example.com/1.8.0/tla2tools.jar", "1.8.0"),
        ("https://example.com/custom/latest/tla2tools.jar", None),
        ("https://example.com/v1.8.0/dist/v2.0.0/tla2tools.jar", "v1.8.0"),
    ],
)
def test_extract_version_from_url(url, expected):
    assert extract_version_from_url(url) == expected
