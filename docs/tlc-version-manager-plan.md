# TLC Version Manager Implementation Plan

This document outlines the step-by-step implementation plan for adding TLC version management capabilities to the `tlaplus-cli` project. It adopts a Test-Driven Development (TDD) approach where unit tests are written first.

## Stage 1: Configuration & CLI Restructuring [X]
**Completion Note:** Implemented config updates, CLI scaffolding, and dummy tests. Encountered an issue where tests expecting `tla tlc <spec>` failed because Typer doesn't support a command and a command-group with the same name (`tlc`). To fix this, part of Stage 4 (`tla run` refactor) was implemented early: the main model checking command was renamed to `tla run`, and integration tests were updated to use it instead of `tla tlc`.
**Goal:** Update the config data models, remove deprecated commands, scaffold the new Typer command subgroups, and set up TDD test infrastructure.
**Details:**
- **Configuration**:
  - Update `TlaUrls` in `settings.py` to include two new GitHub API URLs:
    - `tla.urls.tags` → `https://api.github.com/repos/tlaplus/tlaplus/tags`
    - `tla.urls.releases` → `https://api.github.com/repos/tlaplus/tlaplus/releases`
  - Remove the legacy `nightly` and `stable` mappings.
  - Remove the `jar_name` field from `TlaConfig` — the jar is always `tla2tools.jar` within a version directory.
  - Update `default_config.yaml` accordingly.
- **Refactoring Dead Code**:
  - Delete `src/tlaplus_cli/download_tla2tools.py`.
  - Remove `app.command(name="download")` from `cli.py`.
  - Delete `tests/test_download_tla2tools.py`.
- **Command Routing**:
  - Create a new Typer group: `tlc_app = typer.Typer(help="Manage TLC versions")`.
  - Attach the Typer subgroup: `app.add_typer(tlc_app, name="tlc")`.
  - Wire up empty dummy functions for `list`, `install`, `upgrade`, `find`, `pin`, `dir`, and `uninstall` inside `tlc_app`.
  - Register a new Typer group for cache management: `fetch_cache_app = typer.Typer(help="Manage GitHub API cache")`.
  - Attach it: `app.add_typer(fetch_cache_app, name="fetch-cache")`.
  - Wire up a `clear` command inside `fetch_cache_app`.
- **Test Infrastructure (TDD Foundation)**:
  - Set up test files (e.g., `tests/test_tlc_manager.py`) utilizing Typer's `CliRunner`.
  - Update `conftest.py` `base_settings` fixture so `TlaUrls` uses the new `tags` + `releases` fields instead of `stable`/`nightly`.
  - **Mocking**:
    - Mock `requests.get` to return **two** static JSON responses: one mimicking the Tags API (with `commit.sha` fields) and one mimicking the Releases API (with `assets` download URLs).
    - Mock the file system `cache_dir` so no actual downloading or directory manipulation occurs during these tests.
  - **Test Cases to write** (all expected to fail at this stage):
    - `tla tlc list`: Asserts the output table parses the JSON properly and accurately reports `<version name>  <short tag> <status> <pinned>`.
    - `tla tlc install`: Asserts the correct directory `~/.cache/tla/tlc/<version>-<short_tag>` is created. Asserts auto-pin occurs if no pinned version exists.
    - `tla tlc upgrade`: Asserts the old directory is removed, the new one is created, and the pin shifts.
    - `tla tlc pin`: Asserts the pin is created pointing to the target subdirectory.
    - `tla tlc dir`: Asserts the output is simply the root cache directory.
    - `tla tlc uninstall`: Asserts the directory is recursively deleted. Includes a specific test for `uninstall default` cleaning the legacy jar. Includes a test for uninstalling the pinned version (should warn and clear pin).
    - `tla fetch-cache clear`: Asserts the cache file `~/.cache/tla/github_cache.json` is deleted.
*(At the end of this stage, CLI tests checking arguments should start passing, but semantic tests will still fail).*

## Stage 2: Core Version Manager API (GitHub & OS) [X]
**Completion Note:** Implemented caching strategies and offline-fallback logic into `version_manager.py` with the addition of Enum-based FetchStatus types for accurate UI reporting.
**Goal:** Implement the underlying Python modules (e.g., `tlaplus_cli/version_manager.py`) to interface with the GitHub API and manage local directories, including a caching layer.
**Details:**
- **GitHub API Handler**:
  - Implement `fetch_remote_versions(tags_url, releases_url)` that fetches **both** the Tags API and Releases API, then joins them by tag name (`tags[].name` == `releases[].tag_name`).
  - From Tags API: extract `name` (version) and `commit.sha[:7]` (short tag).
  - From Releases API: extract the `browser_download_url` of the `tla2tools.jar` asset.
  - Return a list of `RemoteVersion` dataclass objects with `name`, `short_sha`, `full_sha`, and `jar_download_url`.
- **API Response Caching**:
  - Cache the combined fetched data as a JSON file at `~/.cache/tla/github_cache.json`.
  - Use a **1-hour TTL**: if the cache file exists and is less than 1 hour old, return cached data instead of making API calls.
  - Implement `clear_cache()` to delete the cache file (used by `tla fetch-cache clear`).
- **Offline / API-Failure Behavior**:
  - Wrap remote fetches in a try/except. On failure (network error, rate limit, timeout):
    - If a cached file exists (even if expired), return stale cached data with a `(cached)` indicator.
    - If no cache exists, return an empty list and let callers display a `⚠ remote data unavailable` warning.
- **Filesystem API Manager**:
  - `get_tlc_dir()`: Returns `cache_dir() / "tlc"`.
  - `list_local_versions()`: Scans `get_tlc_dir()` and parses subdirectories (e.g., splitting `v1.8.0-abcdefg` into its parts).
  - `get_pinned_path()`: Evaluates the symlink at `get_tlc_dir() / "pinned"`.
  - `set_pin(version_dir)`: Helper function to create/overwrite the symbolic link.

## Stage 3: Implementation of TLC Subcommands (Read-Only) [X]
**Completion Note:** Defined read-only Typer commands (`dir`, `list`, `find`, `fetch-cache clear`) incorporating dynamic `rich.table` output for `list`. Fixed a minor Ruff lint requirement by employing ternary operators.
**Goal:** Fulfill the logic for commands that only observe state, plus unit tests for them.
**Details:**
- **`tla tlc dir`**: Output `get_tlc_dir()`.
- **`tla tlc list`**:
  - Fetch available remote versions (via cached fetcher).
  - List local directories.
  - Compare locally installed short tags vs. remote short tags.
  - Output Typer table with dynamic `installed` | `upgrade` | `available` statuses.
  - **Offline behavior**: If remote data is unavailable, show locally installed versions with `installed` or `pinned` status only. Print `⚠ remote data unavailable` warning.
  - **Stale cache**: If using stale cached data, append `(cached)` to the table header.
- **`tla tlc find [<version>]`**: Output the absolute path by resolving directories or defaulting to the `get_pinned_path()`. Handle error cases if not found.
- **`tla fetch-cache clear`**: Delete `~/.cache/tla/github_cache.json` and confirm to the user.
*(At the end of this stage, tests assessing read-only subcommands will pass).*

## Stage 4: `tla run` Refactor [X]
**Completion Note:** Accomplished alias deprecation and runtime re-routing via `cli.py` and `tlc_manager.py`. Built fallback logic bridging new version definitions with old offline setups in `run_tlc.py`.
**Goal:** Migrate the execution command and adapt it to use the new pinned version path, with a legacy fallback for backward compatibility.
**Details:**
- **Command Routing**:
  - In `cli.py`, register the run command: `app.command(name="run")(run_tlc_cmd)`.
  - Keep `tla tlc <spec>` as a **deprecated alias**: register a wrapper command at `app.command(name="tlc")` that prints a deprecation warning (`"Warning: 'tla tlc <spec>' is deprecated, use 'tla run <spec>' instead."`) then delegates to `run_tlc_cmd`. Remove this alias in a future major version.
- **`run_tlc.py` Refactoring**:
  - Modify `src/tlaplus_cli/run_tlc.py`.
  - Use a **fallback chain** for jar resolution:
    ```python
    # Fallback chain: pinned symlink → legacy jar
    pinned = get_tlc_dir() / "pinned" / "tla2tools.jar"
    legacy = cache_dir() / "tla2tools.jar"
    jar_path = pinned if pinned.exists() else legacy
    ```
  - If neither path exists, throw a clear user-facing error urging the user to execute `tla tlc install`.
- **Tests**:
  - Add `tla run <spec>` tests asserting the classpath maps to `pinned/tla2tools.jar` when the pinned directory exists, and falls back to the legacy jar otherwise.
*(At the end of this stage, the `tla run <spec>` tests should pass).*

## Stage 5: Implementation of TLC Subcommands (Mutating) [X]
**Completion Note:** Implemented install, pin, and uninstall commands. Note: When running `pytest` tests automatically, typer prompts (like `uninstall` confirmation) implicitly exit with `1` unless auto-mocked or provided with input. Added `input="y\n"` in `test_tlc_manager.py`.

**Goal:** Implement commands that download assets and manipulate the disk.
**Details:**
- **`tla tlc install [<version>]`**:
  - Lookup the remote tag via the cached fetcher.
  - Fetch the `.jar` asset URL from the `RemoteVersion.jar_download_url`.
  - Stream the download to `~/.cache/tla/tlc/<version>-<short_tag>/tla2tools.jar`.
  - **Auto-pin**: If no pinned version exists, automatically pin the newly installed version. This ensures `tla run` works immediately after the first install.
- **`tla tlc pin [<version>]`**: Wire up `set_pin(...)` allowing users to switch the symlink. Prompt via Typer if duplicate names exist locally.
- **`tla tlc uninstall [<version> | default]`**:
  - Recursively remove `~/.cache/tla/tlc/<version>-<short_tag>`.
  - **Pinned version guard**: If the target version is currently pinned, warn the user with a confirmation prompt: *"Version X is currently pinned. Uninstalling it will break `tla run`. Continue? [y/N]"*. If confirmed, remove the pin symlink and the version directory. Print a follow-up message suggesting `tla tlc pin <other>` or `tla tlc install`.
  - Implement `if version == "default":` to delete `~/.cache/tla/tla2tools.jar` (legacy cleanup).
*(At the end of this stage, tests assessing mutating subcommands will pass).*

## Stage 6: Implementation of TLC Upgrade [X]
**Completion Note:** Formulated the complex logic of resolving old tags vs. new tags using cached API results, dropping down into the `install` task to seamlessly migrate and re-pin versions. The entire plan is now fully integrated.

**Goal:** Address the nuanced upgrade logic.
**Details:**
- **`tla tlc upgrade [<version>]`**:
  - Find the specified (or currently pinned) local version name (e.g., `v1.8.0`).
  - Check the remote GitHub response (via cached fetcher) for `v1.8.0`.
  - If the remote short tag is different from the local one, run the `install` logic for the new tag.
  - If the old version was currently pinned, immediately update the pin to the new directory.
  - Recursively delete the old `<version>-<short_tag>` directory.
*(At the end of this stage, all unit tests established in Stage 1 should pass gracefully!).*
