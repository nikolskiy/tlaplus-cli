# Development Guidelines

## Core Principles

- **Test-Driven Development (TDD):** Write tests before implementation. Every feature or bug fix must be
  accompanied by a failing test that is then made to pass.
- **Pathlib over raw file calls:** The project uses Ruff, which enforces modern path abstractions. Always
  use `with path.open() as f:` instead of the legacy `with open("file") as f:` form to avoid `PTH123`
  lint failures.
- **Subprocess output sanitization:** When parsing output from Java subprocesses, always extract lines
  explicitly (e.g., `result.stdout.strip().split("\n")[0]`) rather than assuming homogeneous returns.
- **Mock heavy I/O in tests:** Use `mocker.patch(...)` to stub out filesystem and network calls in unit
  tests, keeping the test suite fast and free of side effects on the host machine.

---

## Project Architecture & Directory Structure

The `tlaplus_cli` codebase is organized to strictly separate the command-line interface from the core business logic:

1. **`cmd/` Directory (CLI Layer):**
   - The `cmd/` directory represents the concept of providing command-line call support and directly mirrors the actual structure of `tla` CLI commands (e.g., `tla tools list` is wired in `cmd/tools/list.py`).
   - Command groups are defined as directories containing an `__init__.py` (where the `typer.Typer` app is constructed). Actionable leaf commands are standalone `.py` files inside their respective group directory.
   - Code inside `cmd/` should **only** handle argument parsing, user output/input (`typer.echo`, `typer.prompt`), and routing. It must not house domain logic.

2. **Concept Directories (Core Logic Layer):**
   - Business and domain logic resides in top-level concept directories (e.g., `config/`, `cache/`, `versioning/`, `java/`, `tlc/`).
   - These directories do not have command representations and must remain decoupled from `Typer` application logic.
   - When adding new functionality, build the core logic in entirely testable concept modules, and import them into the relevant leaf command in `cmd/`.

---

## Best Practices

### 1. Test Fixtures — Real but Stripped API Data

Use real GitHub API responses (`tests/fixtures/tags.json`, `tests/fixtures/releases.json`) as test
fixtures so that Python parsing is validated against actual nested structures.

**Secret detection prevention:** Before committing fixtures, anonymize all realistic 40-character SHAs
(e.g., replace with `"a" * 40`) and depersonalize user accounts, organization names, and repository
URLs. This avoids triggering secret-scanning workflows while still validating type and length boundaries.

### 2. Pathlib Idioms

The project enforces Ruff rule `PTH123`. Always use:

```python
# correct
with path.open() as f:
    ...

# also correct
with Path("file").open() as f:
    ...

# forbidden — triggers PTH123
with open("file") as f:
    ...
```

### 3. Subprocess Interactions (TLC / Java Calls)

Java tools (e.g., `java -cp tla2tools.jar tlc2.TLC -version`) frequently write help text or error
messages to stdout when unexpected parameters are passed. To avoid storing junk:

- Always strip and split stdout: `result.stdout.strip().split("\n")[0]`
- Capture stderr separately and validate it independently when needed.

### 4. Exception Handling

**Never use `except Exception`.** Every `except` clause must name the narrowest set of exception types
that the protected code can actually raise. Catching `Exception` hides programming errors
(`TypeError`, `AttributeError`, `KeyError`) behind user-facing messages and makes bugs nearly
impossible to diagnose.

Use the following mapping as a guide:

| Operation | Catch |
|---|---|
| File / directory I/O (`open`, `mkdir`, `rename`, `stat`, `unlink`) | `OSError` |
| HTTP requests (`requests.get`, `.raise_for_status()`) | `requests.RequestException` |
| JSON parsing (`json.load`, `json.loads`) | `json.JSONDecodeError` |
| Subprocess invocation (`subprocess.run`) | `subprocess.SubprocessError`, `OSError` |
| Dataclass / model construction from untrusted data | `KeyError`, `TypeError`, `ValueError` |

When multiple failure modes are possible in the same `try` block, combine them in a tuple:

```python
# correct
except (json.JSONDecodeError, OSError, KeyError) as e:
    ...

# forbidden
except Exception as e:
    ...
```

### 5. Try-Block Scoping

A `try` block should contain **only** the statement(s) that can raise the caught exception. All
preparatory work (variable assignments, logging, `typer.echo`) and all follow-up work (displaying
results, constructing paths) must live **outside** the `try/except`.

```python
# correct — only the call that raises is protected
typer.echo("Compiling ...")
try:
    result = compile_modules(base_dir)
except FileNotFoundError as e:
    typer.echo(f"Error: {e}", err=True)
    raise typer.Exit(1) from None
typer.echo(f"Success: {result}")

# forbidden — unrelated statements padded into the try
try:
    typer.echo("Compiling ...")
    result = compile_modules(base_dir)
    typer.echo(f"Success: {result}")
except FileNotFoundError as e:
    ...
```

Similarly, avoid the `try/except/else` pattern when the `except` branch already raises or returns.
In that case the code after `try` naturally acts as the "else" path, and using `else:` only adds
indentation for no benefit.

Do not catch an exception only to `raise` it unchanged — let it propagate naturally:

```python
# forbidden — redundant catch-and-re-raise
except subprocess.CalledProcessError:
    raise

# correct — simply omit the handler; the exception propagates on its own
```

### 6. DRY & Separation of Concerns

- **No logic duplication across layers.** If the same algorithm (e.g., spec-file resolution,
  download-with-progress, metadata writing) appears in more than one function, extract it into a
  single shared helper in the appropriate concept module and call it from both sites.
- **cmd/ must not contain domain logic.** Commands in `cmd/` may only parse arguments, call into
  concept modules, and format output. Resolution, validation, and file-manipulation logic must live
  in the concept layer (`tlc/`, `versioning/`, `config/`, etc.).
- **Helpers must not emit UI output.** Functions that resolve, compute, or validate should return
  results (or raise exceptions). Only the calling command in `cmd/` should decide what to
  `typer.echo`. This ensures helpers remain testable without patching `typer`.
- **Extract common CLI patterns into small utilities.** Repeated micro-patterns such as "auto-pin
  if no version is currently pinned" should be captured in a named helper to avoid copy-paste drift.

### 7. Naming & Public API Hygiene

- **Underscore convention is binding.** A function prefixed with `_` is private to its module. It
  must never be imported by other packages. If another module needs it, either rename it (drop the
  underscore) to make it public, or provide a public wrapper.
- **`__all__` must not list private symbols.** Including `_foo` in `__all__` contradicts the naming
  convention and confuses tooling. Either make the symbol public or remove it from `__all__`.
- **Avoid shadowing builtins.** Do not name modules or imports `list`, `dir`, `type`, etc. If a
  Typer command needs a builtin name, use `@app.command(name="list")` on a differently-named function
  and file (e.g., `show.py`).
- **Consistent field naming in schemas.** Related fields on a Pydantic model should follow a
  uniform naming pattern. Prefer grouping related optional fields into a nested model when their
  count grows.

### 8. Docstrings & Documentation

- **Every public function and class must have a docstring.** This is especially critical for Typer
  commands because Typer uses the docstring as `--help` text. A missing docstring produces a blank
  help description.
- **Docstrings on concept-layer functions** should describe parameters, return values, and any
  exceptions that are raised (following the Google or NumPy style consistently).

### 9. User-Facing Messages

- **Standardize warning format.** All warnings must use the same prefix: `"⚠ Warning: <message>"`,
  written to stderr. Consider using a shared `warn()` helper:
  ```python
  def warn(message: str) -> None:
      typer.echo(f"⚠ Warning: {message}", err=True)
  ```
- **Standardize error format.** All errors must use: `"Error: <message>"`, written to stderr,
  followed by `raise typer.Exit(1)`.
- **Never swallow exceptions silently.** If a `try/except` block intentionally suppresses an error,
  it must still log a warning via `warn()` so the user has observability into failures.

### 10. Pytest Patterns & Typer Mocks

**Isolated test directories:** Pre-create fixture directories (e.g., `installed_v180`, `mock_cache`)
inside the test scope so Typer's `CliRunner` operates in isolation and never touches the host's
`~/.cache` directory.

**Sub-component patching:** When testing functions that loop over installed versions (e.g.,
`tla tools meta sync`), patch out the heavy I/O helpers with `mocker.patch(...)` and assert on
`call_args` directly instead of validating filesystem side effects.

**Advanced Testing Patterns:**

- **Fixture Centralization:** Consolidate shared resources (CLI runners, cache stubs, version factories) in the root `tests/conftest.py`. This ensures a single source of truth for mocks across all sub-suites.
- **Defensive Settings Mutation:** When using a shared `Settings` fixture, always use `base_settings.model_copy(deep=True)` before modifying values. This prevents state leakage between tests.
- **Parametrization:** Prefer `@pytest.mark.parametrize` for functions with multiple edge cases (e.g., URL parsing, version resolution) to reduce code bulk and improve coverage visibility.
- **Mocking Interactive Prompts:** To test interactive CLI flows, patch `typer.prompt` or `typer.confirm`:
  ```python
  mocker.patch("typer.prompt", return_value=1) # Select second option in a menu
  ```
- **Cleanup Validation:** Every function that creates transient files or directories (like `download_version`) must have an accompanying test verifying that those resources are removed on failure (e.g., using `shutil.rmtree` in a `try...except` block).
- **Patch Target Precision:** Patch dependencies in the module they are consumed.
  ```python
  # Correct: Patching subprocess as seen by version_manager
  mocker.patch("tlaplus_cli.version_manager.subprocess.run")
  ```

**Unused unpacked variables:** Suppress `RUF059` warnings by using underscores for intentionally
ignored tuple members:

```python
args, _ = mock.call_args
```