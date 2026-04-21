import re
from collections.abc import Sequence
from urllib.parse import urlparse

from tlaplus_cli.versioning.metadata import read_version_metadata
from tlaplus_cli.versioning.paths import get_tools_dir
from tlaplus_cli.versioning.schema import LocalVersion

_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def is_url(text: str) -> bool:
    """Return True if *text* looks like an HTTP(S) URL."""
    return text.lower().startswith(("http://", "https://"))


def extract_version_from_url(url: str) -> str | None:
    """Scan URL path segments for a semver-like segment (e.g. 'v1.8.0').

    Returns the first matching segment, or None if none is found.
    """
    path = urlparse(url).path
    for segment in path.split("/"):
        if _SEMVER_RE.match(segment):
            return segment
    return None


def _parse_semver(name: str) -> tuple[int, int, int] | None:
    """Try to extract (major, minor, patch) from a version name like 'v1.8.0'."""
    m = _SEMVER_RE.match(name)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def _version_sort_key(lv: LocalVersion) -> tuple[int, tuple[int, int, int], str, float]:
    """
    Build a sort key for determining the "latest" installed version.

    Tuple structure (all compared descending):
      0: has_semver  — 1 if parseable, 0 otherwise (semver > non-semver)
      1: semver      — (major, minor, patch) tuple
      2: published_at — ISO-8601 string from metadata (lexicographic comparison works)
      3: mtime       — directory last-modified timestamp
    """
    semver = _parse_semver(lv.name)
    has_semver = 1 if semver else 0
    semver_tuple = semver if semver else (0, 0, 0)

    published_at = ""
    meta = read_version_metadata(lv.path)
    if meta and meta.get("published_at"):
        published_at = meta["published_at"]

    try:
        mtime = lv.path.stat().st_mtime
    except OSError:
        mtime = 0.0

    return (has_semver, semver_tuple, published_at, mtime)


def resolve_latest_version(versions: Sequence[LocalVersion]) -> LocalVersion | None:
    """Return the 'latest' version from a list, or None if empty.

    Ordering priority:
      1. Highest semantic version wins.
      2. For equal/unparseable semver: latest published_at from meta-tla2tools.json.
      3. For missing metadata: latest directory mtime.
    """
    if not versions:
        return None
    return max(versions, key=_version_sort_key)


def list_local_versions() -> list[LocalVersion]:
    tools_dir = get_tools_dir()
    if not tools_dir.exists():
        return []
    result = []
    for d in tools_dir.iterdir():
        if d.is_dir() and not d.is_symlink():
            # Split on the FIRST hyphen so timestamp suffixes are preserved whole
            parts = d.name.split("-", 1)
            if len(parts) == 2:
                result.append(LocalVersion(name=parts[0], short_sha=parts[1], path=d))
    return result
