# Implementation Plan

## Rename `tlc` command group to `tools`

**Goal:** The `tla2tools.jar` acts as a multi-tool container that includes TLC, SANY (parser), and TLATeX. Renaming the subcommand from `tlc` to `tools` clarifies that these commands manage the entire toolset distribution rather than solely the TLC model checker.

### 1. Renaming the Subcommand App (`cli.py`, `tlc_manager.py` -> `tools_manager.py`)
- Rename the file `src/tlaplus_cli/tlc_manager.py` to `src/tlaplus_cli/tools_manager.py`.
- In `tools_manager.py`, rename the Typer instance from `tlc_app` to `tools_app`.
- In `tools_manager.py`, update all decorators from `@tlc_app.command()` to `@tools_app.command()`.
- In `src/tlaplus_cli/cli.py`, update the import to point to `tools_manager`. Change the typer group mapping from `app.add_typer(tlc_app, name="tlc")` to `app.add_typer(tools_app, name="tools")`.

### 2. Update Internal State and Directory Names (`version_manager.py`)
Since the tool manipulates the `tla2tools.jar` (which contains multiple tools, not just TLC), we should generalize its caching directories:
- Rename the cache folder from `cache_dir() / "tlc"` to `cache_dir() / "tools"`.
- Rename the function `get_tlc_dir()` to `get_tools_dir()`.
- Rename the pinning file from `tlc-pinned-version.txt` to `tools-pinned-version.txt`.
- Add legacy migration logic in `_migrate_legacy_pin` to safely handle moving an existing `~/.cache/tlaplus-cli/tlc` to `~/.cache/tlaplus-cli/tools` if one exists, ensuring users don't have to re-download jars they already installed.

### 3. Update Tests
- Rename the test file `tests/test_tlc_manager.py` to `tests/test_tools_manager.py`.
- In `tests/test_tools_manager.py`, replace all CLI `runner.invoke(app, ["tlc", ...])` calls with `runner.invoke(app, ["tools", ...])`.
- Update all occurrences of the mocked paths in the tests from `tmp_path / "tlc"` to `tmp_path / "tools"`.
- Update references in `tests/test_run_tlc.py` and other test files that mock cache paths or use `tlaplus_cli.tlc_manager` imports.

### 4. Update Documentation and Changelog
- Update `CHANGELOG.md` to reflect the command renaming (e.g., `tla tlc <action>` -> `tla tools <action>`) under the upcoming release section.
- Review and update the main `README.md`, replacing old command usages `tla tlc ...` with `tla tools ...`.
- Scan the `docs/` folder (such as `development.md`, `quick-module-overview.md`) for mentions of `tla tlc` or `tlc_manager.py` and update them accordingly.

### 5. Validation
- Run tests using `uv run pytest` to ensure the rename didn't break existing functionality.
- Run linters using `uv run poe lint` to verify type and style checks.
