# Scratchpad: TLC Version Manager Plan

## Core Architecture and Configuration
- **Configuration Update**: 
  - Update `default_config.yaml` and properties in `settings.py`. 
  - Remove the `nightly` build options completely.
  - Instead of hardcoding JAR URLs, the config (e.g. `tla.urls.stable` or `tla.urls.releases`) will point to the GitHub Releases API URL: `https://api.github.com/repos/tlaplus/tlaplus/releases`.
- **Fetching Releases**: 
  - Fetch available versions and download assets (the `tla2tools.jar` files) using the GitHub Releases API.
  - *Example API request:* `curl -H "Accept: application/vnd.github+json" https://api.github.com/repos/tlaplus/tlaplus/releases` (to be implemented in Python).
- **Directory Structure**: 
  - Each installed version will be stored in a separate directory within the cache (e.g., `~/.cache/tla/tlc/<version_name>-<short_tag>/`).
- **Pinning Mechanism**: 
  - Pinning is managed via a symbolic link. A symlink (e.g., `~/.cache/tla/tlc/pinned`) will point to the specific version directory of the active pinned version.

## `tla tlc` Command Group
The `tla tlc` command group will manage your TLC installations.

- **`tla tlc list`**: List available TLC installations.
  - **Output Format**: `<version name>  <short tag>  <status>  <pinned>`
  - **Version name**: Retrieved from the "name" field in the GitHub release JSON (e.g., `v1.8.0`, `v1.7.4`).
  - **Short tag**: The first 7 characters of the release commit SHA.
  - **Status**: 
    - `installed` if the locally installed short tag matches the remote tag.
    - `upgrade` if the version is installed locally but there is a newer release with the same version name but a different short tag.
    - `available` if it is not installed locally.
  - **Pinned**: Displays a green checkmark if the version is pinned, otherwise left blank.

- **`tla tlc install [<version_name> | <short_tag>]`**: Download and install a TLC version.
  - If no version or tag is provided, installs the latest version.
  - Creates the versioned directory (e.g., `v1.8.0-abcdefg`) and stores the downloaded JAR there.

- **`tla tlc upgrade [<version_name>]`**: Upgrade an installed TLC version.
  - *Context:* Some releases (like `v1.8.0`) retain the same version name while their short tags update.
  - **Behavior**: Checks if there is a newer short tag for the given version name. If so, it downloads the new version to a new directory, updates the pin symlink (if that version was currently pinned), and completely removes the old version directory.
  - If no argument is provided, it upgrades the currently pinned version by default.

- **`tla tlc find [<version_name>]`**: Search for a TLC installation path.
  - Outputs the absolute path to the `tla2tools.jar` of the requested version.
  - If no version is provided, outputs the path to the pinned version.
  - *Example Output:*
    ```text
    TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)
    /home/bob/.cache/tla/tlc/v1.8.0-5a47802/tla2tools.jar
    ```

- **`tla tlc pin [<version_name>]`**: Pin to a specific TLC version.
  - Pinning is done using the version name. If multiple copies of the same release name exist locally, prompt the user to choose by short tag.
  - If no argument is provided, pins the latest installed version.

- **`tla tlc dir`**: Show the root TLC installation directory.
  - *Example Output:* `/home/bob/.cache/tla/tlc`

- **`tla tlc uninstall <version_name> | <short_tag> | default`**: Uninstall TLC versions.
  - Removes the directory associated with the selected version.
  - **Migration & Cleanup:** Supplying the special argument `default` deletes the legacy, unversioned `~/.cache/tla/tla2tools.jar` file leftover from older CLI versions.

## Other Commands
- **`tla run <spec>`**: 
  - **[UPDATED]** Replaces `tla tlc <spec>`. Executes the TLC model checker on a TLA+ specification using the currently pinned version of TLC.
- **`tla download`**: 
  - **[REMOVED]** Removed entirely. It is superseded by the `tla tlc install` commands.
- **`tla check-java`**: Verify Java version meets the minimum requirement. *(Already exists)*
- **`tla build`**: Compile custom Java modules for TLC. *(Already exists)*