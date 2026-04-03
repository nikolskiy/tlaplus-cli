# Implementation Plan: Rename `tla run` to `tla tlc`

## Objective
Replace the `run` command with `tlc` so that users run the model checker via `tla tlc <spec>` instead of `tla run <spec>`. This clarifies the purpose of the command because `tla2tools` supports other tools alongside TLC.

## 1. Update CLI Entrypoint
- In `src/tlaplus_cli/cli.py`, change the command registration from `app.command(name="run")(run_tlc_cmd)` to `app.command(name="tlc")(run_tlc_cmd)`.

## 2. Update Internal Code References
- In `src/tlaplus_cli/tools_manager.py`, update strings referring to `tla run` such as: "will break `tla run`" -> "will break `tla tlc`".

## 3. Update Tests
- In `tests/test_run_tlc.py`, update test cases to invoke `tlc` instead of `run`:
  - Change `runner.invoke(app, ["run", "queue"])` to `runner.invoke(app, ["tlc", "queue"])`
  - Change `runner.invoke(app, ["run", "--version"])` to `runner.invoke(app, ["tlc", "--version"])`
- Update the docstrings in the test file reflecting `tla run`.

## 4. Update Documentation
- **README.md**:
  - Update usage examples from `tla run <spec_name>` to `tla tlc <spec_name>`.
  - Update the command history note that mentions the older structue.
- **docs/module-how-to.md**: Update commands like `tla run queue` to `tla tlc queue` and fix related descriptions.
- **docs/quick-module-overview.md**: Change `tla run queue` to `tla tlc queue`.
- **verify**: verify that all docs files have a correct version of the command.

## 5. Update Changelog
- **CHANGELOG.md**: Add a new specific entry under the [Unreleased] or current target version section noting that `tla run` has been renamed to `tla tlc` to better reflect its function, since the old `tlc` command group was renamed to `tools`.

## 6. Validation
- Run tests using `uv run pytest` to ensure the rename didn't break existing functionality.
- Run linters using `uv run poe lint` to verify type and style checks.
- Manually run `uv run tla tlc --help` to confirm the CLI help is updated appropriately.
