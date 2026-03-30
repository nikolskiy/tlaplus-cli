# Scratchpad

## Fixes and Improvements

### [x] Group 1: Core Metadata Storage
- **Metadata Storage:** When a new version is downloaded (via install or upgrade), save all available meta information (release date, sha, version string from `java -cp tla2tools.jar tlc2.TLC -version`, etc.) in a `meta-tla2tools.json` file in the same directory as the jar. The following fields should be saved:
    - `tag_name`: The tag name from the repository (e.g., "v1.8.0"). Serves as the primary identifier.
    - `sha`: The exact commit SHA from the `tags` endpoint. Crucial for pinpointing the exact codebase state.
    - `published_at`: The release date from the `releases` endpoint (ISO 8601). Used for sorting and fallback logic.
    - `tlc2_version_string`: Generated locally via `java -cp tla2tools.jar tlc2.TLC -version`.
    - `prerelease`: Boolean from the `releases` endpoint to identify beta/RC versions.
    - `download_url`: The `browser_download_url` for the jar from the `releases` endpoint.
- **Metadata Resync Command:** Create a `tla tlc meta sync` command that iterates over all locally installed versions and regenerates their `meta-tla2tools.json` files. This is necessary to easily backfill metadata if future updates require capturing additional information.

### [x] Group 2: Command Renaming and Output Enhancements (`find` -> `path`, `dir`)
*Development Approach: Use TDD. Write unit tests utilizing mock setups to verify standard CLI output logic against internal metadata caches.*
- **Rename "find":** Rename "find" to "path". The name "find" is confusing because it implies searching for any version, a functionality that isn't present.
- **`path` Output Modification:** The new `path` command should show the path to the jar alongside the synthesized TLC2 version string from our internal `meta-tla2tools.json` cache metadata (captured initially during download). Example:
    ```text
    TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)
    /home/bob/.cache/tla/tlc/v1.8.0-5a47802/tla2tools.jar
    ```
- **`dir` Output Modification:** `tla tlc dir` should show the path to the directory as well as its contents (the list of installed version directories).

### Group 3: Pin State Management & Auto-Pinning
*Core state logic that ensures the pinned version is always valid.*
*Development Approach: Use TDD. Write explicit tests for auto-pin interactions and verify the fallback logic through simulated `meta-tla2tools.json` dates and filesystem timestamps.*
- **Auto-pinning on Install:** When a version is installed and no version is currently pinned, it should automatically be used as the pinned version. There should not be a state where versions are installed but no version is pinned.
- **Pin Stability:** Make sure that if a version is pinned and another version is installed, the pinned version doesn't change. Write a test for these cases.
- **Fallback Logic (on Uninstall):** If a pinned version is uninstalled, the pin should fall back and point to the "latest" installed version. If no version is installed, the pin should be removed entirely. The "latest" version is determined by first parsing semantic versioning. If versions are identical (or non-semver like `nightly`), fall back to the release date from `meta-tla2tools.json`. If the release date is not available, fall back to the directory's last-modified timestamp.

### Group 4: `list` & `upgrade` Command Improvements
*Refining list display and the upgrade process, interacting with metadata and pin states.*
*Development Approach: Use strict TDD. Use `tests/fixtures/releases.json` and `tests/fixtures/tags.json` as API response mocks to accurately construct and verify the `list` aesthetics and edge case `upgrade` behavior.*
- **Status Display:** The `list` should not show an intermediate "upgrade" state. The status should strictly be "installed" (if it is locally present) or "available" (if it's on GitHub but not downloaded).
- **Tag Discrepancy:** If there is a version with the same name (e.g., `v1.8.0`) but a different tag from an already installed one available, show that available version in the table alongside the installed one.
- **Aesthetics & Enhancements:**
    - To `tla tlc list` add the date when the version was released (using `meta-tla2tools.json`).
    - The pinned column of the list should show a green checkmark instead of "yes".
- **Upgrade Behavior:** `tla tlc upgrade` fixes:
    - If no version name is provided, determine the target version name from the current pin (e.g., if `1.7.4` is pinned, upgrade only `1.7.4` to its latest available tag).
    - If a version name like `v1.8.0` is provided and a newer tag is available, update it to the new tag.
    - If upgrade is called on the currently pinned version, the pin should automatically point to the newly downloaded tag.
    - If the target version to upgrade is unexpectedly not installed locally, just install it.

### Group 5: `uninstall` Command Logic
*Safe uninstallation with interactive prompts.*
*Development Approach: Use TDD. Use testing utilities to mock user inputs via CLI runners, ensuring complete command safety across multiple version uninstall scopes (like `--all`).*
- **Interactive Prompts:** Uninstall currently removes all available tags matching the single version name. It should interactively ask which specific version to uninstall using a standard prompt with a numbered list (similar to the `pin` command) when there are multiple installed tags for that version name.
- **All Flag:** It should take an `--all` flag to bypass the prompt and remove all versions under that name. Write a test for this behavior.