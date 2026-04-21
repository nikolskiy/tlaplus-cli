# Implementation Plan: Restructuring `tlaplus_cli`

**Goal**: Restructure the `tlaplus_cli` source codebase into a dual architecture: a `cmd/` directory reflecting the command-line structure, and separate concept directories handling core logic. This ensures domain logic is isolated from Typer CLI logic.

**Core Rule**: We must not change the behavior or assertions of the existing test suite. The project relies on existing tests to verify system stability during the restructure. The only permitted test modifications are updating `import` statements and updating `mocker.patch(...)` target strings to point to the new package locations. We will actively run `uv run pytest` and `uv run poe lint` after every step to catch regressions immediately.

## Phase 1: Extract Concepts (Core Logic Separation)

**Objective**: Move domain logic out of CLI modules to prevent CLI pollution and improve testability.

*   **Step 1.1**: Create concept directories within `src/tlaplus_cli/`: `cache/`, `config/`, `java/`, `project/`, `tlc/`, and `versioning/`. Ensure each has an `__init__.py`.
*   **Step 1.2**: Extract configuration handling. Create `config/schema.py` and `config/loader.py` to hold data from `settings.py` and `config.py`. Update all imports across the app and tests. Run `uv run pytest` and `uv run poe lint`.
*   **Step 1.3**: Extract versioning logic. Move downloading, validation, resolving paths, and metadata manipulation from `version_manager.py` into `versioning/`. Run `pytest` and `lint`.
*   **Step 1.4**: Extract API caching logic into `cache/`. Run `pytest` and `lint`.
*   **Step 1.5**: Extract Java inspection logic from `check_java.py` to `java/` taking care to handle the `subprocess` outputs correctly per `docs/development.md`. Run `pytest` and `lint`.
*   **Step 1.6**: Extract module building/compilation logic from `build_tlc_module.py` into `tlc/compiler.py` and actual TLC running logic from `run_tlc.py` to `tlc/runner.py`. Move `project.py` logic into `project/`. Run `pytest` and `lint`.

## Phase 2: Scaffold Commands (`cmd/`)

**Objective**: Set up the target CLI structure matching the commands without breaking existing flat file entrypoints yet.

*   **Step 2.1**: Create the `src/tlaplus_cli/cmd/` hierarchy.
    *   Initialize top-level subcommands: `check_java.py`, `tlc.py`.
    *   Create group folders with `__init__.py` files:
        *   `cmd/config/`
        *   `cmd/fetch_cache/`
        *   `cmd/modules/`
        *   `cmd/tools/`
        *   `cmd/tools/meta/`
*   **Step 2.2**: Set up Typer sub-groups in the `__init__.py` files. Create an empty `typer.Typer` in `cmd/tools/__init__.py`, `cmd/modules/__init__.py`, etc.

## Phase 3: Relocate Leaf Commands

**Objective**: Migrate the CLI callback logic into the newly scaffolded structure.

*   **Step 3.1**: Migrate `config` CLI. Move `list` and `edit` commands to `cmd/config/list.py` and `cmd/config/edit.py`. Update tests pointing to `config_cli.py`. Run `pytest` and `lint`.
*   **Step 3.2**: Migrate `modules` CLI. Move `build`, `path`, and `lib` to `cmd/modules/build.py`, `cmd/modules/path.py`, and `cmd/modules/lib.py`. Run `pytest` and `lint`.
*   **Step 3.3**: Migrate `tools` CLI. Move `list`, `install`, `upgrade`, `path`, `pin`, `dir`, and `uninstall` commands from `tools_manager.py` to their respective `.py` files inside `cmd/tools/`. Update patching targets in tests. Run `pytest` and `lint`.
*   **Step 3.4**: Migrate `tools meta` CLI. Move `sync` string into `cmd/tools/meta/sync.py`.
*   **Step 3.5**: Migrate `fetch-cache` CLI into `cmd/fetch_cache/clear.py`.
*   **Step 3.6**: Migrate root commands. Move the `tlc` and `check_java` Typer commands into `cmd/tlc.py` and `cmd/check_java.py`.

## Phase 4: Main Entry Point Migration

**Objective**: Connect the CLI directly to the `cmd/` structure and remove original files.

*   **Step 4.1**: Update `src/tlaplus_cli/cli.py`. Swap the imports from the old specific files to import the Typer instances initialized in `cmd`.
*   **Step 4.2**: Verify `tla --help` successfully loads the full tree.
*   **Step 4.3**: Remove Old Modules. Delete `version_manager.py`, `tools_manager.py`, `config_cli.py`, `check_java.py` (the top level one), `build_tlc_module.py`, `run_tlc.py`.
*   **Step 4.4**: Final Verification. Run `uv run pytest` to guarantee all tests pass efficiently, and ensure 100% `poe lint` compliance with correct `pathlib` rules and no `RUF059` warnings.
