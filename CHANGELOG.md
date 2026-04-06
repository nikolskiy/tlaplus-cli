# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.3.3] - 2026-04-06

### Fixed
- Resolved `FileNotFoundError` when loading the default configuration in certain installation environments (e.g., `uv tool install`) by switching to `importlib.resources` for robust package data access.

## [0.3.2] - 2026-04-03

### Added
- `tla tlc` now intelligently resolves `<spec>` files:
  - Supports running without the `.tla` extension.
  - Automatically checks for files inside a `spec/` subdirectory relative to the specification path.
  - Provides a detailed error message listing all checked locations when a specification cannot be found.
- `tla tlc --version`: Added a flag to display the absolute path to the currently pinned `tla2tools.jar` and its internal TLC version string.
- Project-aware TLA+ support:
  - `tla tlc` now automatically discovers project roots by looking for `modules/`, `classes/`, or `lib/` directories adjacent to the spec or its parent.
  - TLC's classpath now includes the project's `classes/` directory and any `*.jar` files found in the project's `lib/` directory.
  - `-DTLA-Library` is automatically set to the project's `modules/` directory if it exists.
- `tla modules build`:
  - Added an optional `[PATH]` argument to specify the project root (defaults to workspace root).
  - Automatically includes `lib/*.jar` files from the project root in the `javac` classpath.

### Changed
- `tla build` renamed to `tla modules build` for better command organization.
- `tla tools path`: Output now strictly emits the absolute path to `tla2tools.jar` only, removing the TLC version string to better support scripting and piping.


## [0.3.1] - 2026-04-03

### Added
- **System CA Support**: Integrated `truststore` to automatically utilize the native OS certificate store for network requests. This resolves SSL verification failures in environments with custom CAs (e.g., corporate proxies).
- **Breaking Change**: Renamed the `run` command to `tlc` to better reflect its function, since the previous `tlc` command group was renamed to `tools`.

  - To run the model checker, use `tla tlc <spec>` instead of `tla run <spec>`.
- **Breaking Change**: Renamed the `tlc` subcommand group to `tools` to better reflect that it manages the entire TLA+ toolset distribution (TLC, SANY, TLATeX).
  - `tla tlc <action>` is now `tla tools <action>`.
  - Internal cache directory moved from `~/.cache/tlaplus-cli/tlc` to `~/.cache/tlaplus-cli/tools`.
  - Pin file renamed to `tools-pinned-version.txt`.
  - Automatic migration of existing cache and pins is performed on first run.
- Intelligent pin state management:
  - **Auto-pinning**: The first toolset version installed is now automatically pinned.
  - **Pin stability**: Subsequent installations of other versions will no longer "hijack" the current pin.
  - **Smart Fallback**: Uninstalling the pinned version now automatically re-pins the "latest" remaining version based on semantic versioning, release date, or directory age.
- `uninstall`: Added `--all` flag to remove all tags for a specific version name.
- `uninstall`: Added interactive selection when multiple tags exist for the same version name.
- `upgrade`: Now seamlessly installs the target version if it is not already present locally.

### Changed
- `list`: Enhanced table display with a "Published" column and a green checkmark `✓` for the pinned version.
- `list`: Improved version resolution to show separate entries for different SHAs of the same version name, removing the confusing "upgrade" status.
- `upgrade`: Now defaults to upgrading the currently pinned version if no version argument is provided.
- `upgrade`: Automatically updates the pin to the new directory if the version being upgraded was currently pinned.
- `pin` & `uninstall`: Matching versions are now sorted by directory name for consistent interactive selection.

## [0.2.1] - 2026-03-30

### Added
- Comprehensive TLC version management under the `tla tlc` command group.
  - `list`: Show available remote versions and locally installed versions.
  - `install`: Download specific or latest TLC versions directly from GitHub.
  - `pin`: Set a default version to use across the workspace.
  - `upgrade`: Update the pinned version to a newer commit.
  - `path`: Get the absolute path to the local `tla2tools.jar` for the pinned or a specific version. Displays the TLC2 version string from cached metadata above the path when available.
  - `dir`: Show the TLC versions directory and list all installed version directories.
  - `uninstall`: Remove local versions to free up space.
  - `meta sync`: Backfill or rebuild `meta-tla2tools.json` metadata profiles for existing local installations.
- Robust local TLC version profile generator saving metadata like parsed dates and `java -cp` output headers via `meta-tla2tools.json`.
- Added GitHub API caching with a 1-hour TTL to avoid rate limits (manageable via `tla fetch-cache clear`).
- Added `--force` flag for re-downloading versions.
- Added a visual progress bar for TLC jar downloads.

### Changed
- **Breaking Change**: The main execution command has been renamed from `tla tlc <spec>` to `tla run <spec>` to support the new `tlc` subcommand group.
- Migrated legacy `tla2tools.jar` handling. The old `tla download` command has been removed.
- Refactored `tlaUrls` in `config.yaml` to point to GitHub tags and releases endpoints directly.
- Use a plain text marker (`tlc-pinned-version.txt`) for tracking the pinned TLC version to ensure cross-platform compatibility (avoiding Windows symlink requirements).

### Fixed
- Significantly expanded the test suite to use robust mock fixtures for GitHub API and filesystem side-effects.


## [0.1.8] - 2026-03-18

### Changed

- Refactored `tla` source directory to use the standard Python `src/tlaplus_cli` layout.
- Renamed the internal Python package to `tlaplus_cli` to avoid global namespace collisions on PyPI while keeping the external `tla` CLI command name.
- Improved tests.

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
