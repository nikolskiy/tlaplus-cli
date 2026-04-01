# Implementation Plan

This document outlines the detailed implementation plan for Group 4 and Group 5 features as defined in `docs/scratch.md`, adhering to the standard project development guidelines inside `docs/development.md`.

## Group 4: `list` & `upgrade` Command Improvements

This group focuses on refining the list display and the upgrade process, interacting with metadata and pin states. It relies on strict Test-Driven Development (TDD), using `tests/fixtures/releases.json` and `tests/fixtures/tags.json` to accurately mock API responses for both commands.

### Phase 4.1: Enhancing the `list` Command

**Objective:** Clean up the status display, handle tag discrepancies, and improve aesthetics (release dates and green checkmarks).

1.  **Status Display & Tag Discrepancy Update:**
    -   *Current Behavior:* `list_versions` (in `src/tlaplus_cli/tlc_manager.py`) sets the status to `"upgrade"` if the short SHA doesn't match the installed version's short SHA.
    -   *Desired Behavior:* The `list` should not display an "upgrade" state, and it should accurately handle a version name (like `v1.8.0`) that has different tags locally vs remotely. If there is a remote version whose tag/SHA differs from the locally installed version with the same name, both should appear in the list.
    -   *Implementation:*
        -   Iterate over remote versions. If a remote version does not exist locally with the exact same SHA, mark it as "available". If it exists with the exact same SHA, mark it as "installed".
        -   Iterate over local versions. Mark them all as "installed" (and handle cases where they are local-only).
        -   Ensure there are no duplicates. A local version and a remote version with the same name but different SHAs will be separate list entries.
2.  **Aesthetics (Release Date & Pinned Checkmark):**
    -   *Release Date:* Add a "Published" column to the `rich.Table`. For remote versions, use `v.published_at` (formatted nicely, e.g., dropping the time portion if appropriate). For local versions (especially in offline/unavailable mode or if they are local-only), read it from `meta-tla2tools.json` via `read_version_metadata(lv.path).get("published_at")`.
    -   *Pinned Column Checkmark:* Modify `is_pinned` logic to show a green checkmark `[green]✓[/green]` rather than `"Yes"`.
3.  **TDD Steps for 4.1:**
    -   Write a test using `tests/fixtures/tags.json` and `tests/fixtures/releases.json`. Setup a mock local directory with a different SHA than the remote one.
    -   Assert that the table contains separate entries for the remote and local versions, both indicating correct statuses ("available" and "installed"), and that no "upgrade" status exists.
    -   Write a test verifying the display of the green checkmark and the published dates. Must use mocked `meta-tla2tools.json` reads.

### Phase 4.2: Refining the `upgrade` Command

**Objective:** Update `upgrade` to intuitively target only the requested version, correctly auto-update the pin, and handle missing local targets gracefully.

1.  **Default to Pinned Version:**
    -   If `upgrade(version=None)` is called without an argument, the default should fallback to upgrading the currently pinned version.
    -   Obtain the base `name` (e.g., `v1.8.0`) from the pinned directory name to serve as the target.
2.  **Target Specific Version & Tag Updating:**
    -   Resolve the target version name (like `v1.8.0`) to its newest available remote tag (SHA). This is already mostly handled, but verify that it correctly uses the remote short SHA.
3.  **Automatic Application & Missing Local Install:**
    -   *Current behavior:* `upgrade` throws an error ("Version X not found locally") if the version is not found locally.
    -   *Desired behavior:* If the target version to upgrade is unexpectedly not installed locally, seamlessly install it (effectively calling or duplicating the `install` logic).
4.  **Pin Upgrading:**
    -   If the old directory being upgraded was the currently pinned directory, automatically repin to the newly downloaded directory (`new_dir`).
5.  **TDD Steps for 4.2:**
    -   Use isolated test directories and mock network/heavy I/O (`mocker.patch(..., autospec=True)`).
    -   Write test `test_upgrade_no_args_upgrades_pinned_version`.
    -   Write test `test_upgrade_existing_version_with_newer_remote_tag`.
    -   Write test `test_upgrade_missing_local_version_triggers_install`.

---

## Group 5: `uninstall` Command Logic

This group focuses on safe, interactive uninstallation, ensuring users don't accidentally wipe out multiple tags of the same version without confirmation, and providing an `--all` flag for bulk action.

### Phase 5.1: Interactive Uninstallation

**Objective:** Prompt the user when multiple local directories match a single version name.

1.  **Detecting Multiple Tags:**
    -   Currently, `uninstall(version: str)` in `tlc_manager.py` loops over all `matching = [lv for lv in local_versions if lv.name == version]` and blindly deletes all of them.
    -   Modify this behavior: if `len(matching) > 1` and the `--all` flag is not passed, use a `typer.prompt` to interactively list the matching versions (e.g., `[0] v1.8.0-abcd123`, `[1] v1.8.0-efgh456`) and ask the user which single one they want to remove.
2.  **Handling the User Choice:**
    -   Parse the user's integer choice (similar to the logic in `pin`).
    -   Execute the uninstallation and pin-fallback logic *only* on the selected directory.
3.  **Preserving Pinned Fallback:**
    -   If the chosen version to uninstall is pinned, request confirmation (as it currently does), then utilize `resolve_latest_version` to fallback the pin automatically.

### Phase 5.2: The `--all` Flag

**Objective:** Provide a flag to bypass the prompt and remove all tags for a version name.

1.  **Add `--all` Toggle:**
    -   Update the command signature to: `def uninstall(version: str = typer.Argument(None), all: bool = typer.Option(False, "--all", help="Remove all matching versions."))`
2.  **Apply Logic:**
    -   If `all=True`, skip the interactive prompt and remove all elements in `matching`, iterating through each to handle unpinning and deleting.
    -   Apply the post-uninstall fallback logic correctly if the pinned version was among those deleted.
3.  **TDD Steps for 5.1 & 5.2:**
    -   Use `typer.testing.CliRunner(mix_stderr=False)` passing `input="0\n"` to test the interactive selection of `[0]`.
    -   Write a test using the `--all` flag to assert `shutil.rmtree` is called for every matched local version.
    -   Ensure `mocker.patch` targets `shutil.rmtree` to prevent actual deletion of vital directories outside test fixtures. Make sure tests isolate `cache_dir()`.
