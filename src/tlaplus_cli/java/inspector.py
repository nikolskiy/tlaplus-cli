"""Java inspection utilities."""

import re
import shutil
import subprocess


def get_java_version() -> str | None:
    """Get the installed Java version string using 'java -version'."""
    java_executable = shutil.which("java")
    if not java_executable:
        return None

    try:
        # java -version prints to stderr
        result = subprocess.run(
            [java_executable, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Combine stdout and stderr just in case
        output = result.stderr + result.stdout

        # Look for version string like "1.8.0_202" or "11.0.2" or "17"
        # Output typically starts with: openjdk version "11.0.2" ...
        # Correctly handle subprocess outputs as per docs/development.md
        # but here we use regex on the whole output which is fine.
        match = re.search(r'version "(\d+(\.\d+)*(_\d+)?(-\w+)?)"', output)
        if match:
            return match.group(1)

        # Fallback for some distributions that might minimal output
        match = re.search(r"version (\d+(\.\d+)*)", output)
        if match:
            return match.group(1)

    except (subprocess.SubprocessError, OSError):
        pass

    return None


def parse_java_version(version_str: str) -> int:
    """Parse major Java version from string.

    Examples:
    - "1.8.0_202" -> 8
    - "11.0.2" -> 11
    - "17" -> 17
    """
    parts = version_str.split(".")
    if parts[0] == "1":
        # legacy format 1.x
        if len(parts) > 1:
            return int(parts[1])
        return 1  # Fallback, though unlikely
    return int(parts[0])


def validate_java_version(min_version: int) -> None:
    """Check if installed Java version is at least min_version.

    Raises:
        RuntimeError: if Java is not found or version is too low.
    """
    version_str = get_java_version()

    if not version_str:
        msg = f"Java {min_version}+ not found. Please install Java."
        raise RuntimeError(msg)

    try:
        major_version = parse_java_version(version_str)
    except (ValueError, IndexError):
        # Warning is handled in CLI
        return

    if major_version < min_version:
        msg = f"Java {min_version}+ required; found {version_str}."
        raise RuntimeError(msg)
