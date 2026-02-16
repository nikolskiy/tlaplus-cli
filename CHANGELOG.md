# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.6] - 2026-02-16

### Added

- Automated release workflow (`.github/workflows/release.yml`) for GitHub Releases and PyPI publishing.
- `scripts/release.sh` helper script to simplify version bumping and tagging.

### Fixed

- Corrected invalid PyPI classifier (`Topic :: Utilities`) that caused upload failures.
- Added comprehensive test suite execution (Java check, linting, tests) to the release workflow.

## [0.1.3] - 2026-02-16

### Added

- Metadata for PyPI release.

## [0.1.1] - 2026-02-16

### Fixed

- Fixed `--version` flag to correctly read package metadata after `uv tool install`.

## [0.1.0] - 2026-02-13

### Added

- `tla download` — download stable or nightly `tla2tools.jar`.
- `tla check-java` — verify Java version meets the minimum requirement.
- `tla build` — compile custom Java modules for TLC.
- `tla tlc <spec>` — run the TLC model checker on a specification.
- Automatic config creation on first run (`~/.config/tla/config.yaml`).
- Pydantic-based configuration with `JAVA_OPTS` environment variable support.
