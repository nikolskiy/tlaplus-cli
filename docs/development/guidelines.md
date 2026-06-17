# Development Guidelines

> **Scope:** These guidelines apply to any Python CLI project built with
> [Typer](https://typer.tiangolo.com/) (or a similar framework), linted with
> [Ruff](https://docs.astral.sh/ruff/), and tested with
> [pytest](https://docs.pytest.org/). Adjust tool names if your stack differs.

## Core Principles

- **Test-Driven Development (TDD):** Write tests before implementation. Every feature or bug fix must be
  accompanied by a failing test that is then made to pass.
- **Pathlib over raw file calls:** Ruff enforces modern path abstractions. Always
  use `with path.open() as f:` instead of the legacy `with open("file") as f:` form to avoid `PTH123`
  lint failures.
- **Subprocess output sanitization:** When parsing output from external subprocesses, always extract
  lines explicitly (e.g., `result.stdout.strip().split("\n")[0]`) rather than assuming homogeneous
  returns.
- **Mock heavy I/O in tests:** Use `mocker.patch(...)` to stub out filesystem and network calls in unit
  tests, keeping the test suite fast and free of side effects on the host machine.

---

## Project Architecture & Directory Structure

The project codebase is organized to strictly separate the command-line interface from the core business logic:

1. **`cmd/` Directory (CLI Layer):**
   - The `cmd/` directory represents the concept of providing command-line call support and directly mirrors the actual structure of CLI commands (e.g., `mycli items list` is wired in `cmd/items/list.py`).
   - Command groups are defined as directories containing an `__init__.py` (where the `typer.Typer` app is constructed). Actionable leaf commands are standalone `.py` files inside their respective group directory.
   - Code inside `cmd/` should **only** handle argument parsing, user output/input (`typer.echo`, `typer.prompt`), and routing. It must not house domain logic.

2. **Concept Directories (Core Logic Layer):**
   - Business and domain logic resides in top-level concept directories (e.g., `config/`, `cache/`, `services/`).
   - These directories do not have command representations and must remain decoupled from `Typer` application logic.
   - When adding new functionality, build the core logic in entirely testable concept modules, and import them into the relevant leaf command in `cmd/`.

---

## Best Practices

### 1. Test Fixtures — Real but Stripped API Data

Use real API responses (e.g., `tests/fixtures/api_response.json`) as test
fixtures so that Python parsing is validated against actual nested structures.

**Secret detection prevention:** Before committing fixtures, anonymize all realistic tokens or hashes
(e.g., replace 40-character SHAs with `"a" * 40`) and depersonalize user accounts, organization names,
and repository URLs. This avoids triggering secret-scanning workflows while still validating type and
length boundaries.

### 2. Pathlib Idioms

Ruff rule `PTH123` is enforced. Always use:

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

### 3. Subprocess Interactions

External tools frequently write help text or error messages to stdout when unexpected parameters are
passed. To avoid storing junk:

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
preparatory work (variable assignments, logging, user output) and all follow-up work (displaying
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

- **No logic duplication across layers.** If the same algorithm (e.g., file resolution,
  download-with-progress, metadata writing) appears in more than one function, extract it into a
  single shared helper in the appropriate concept module and call it from both sites.
- **`cmd/` must not contain domain logic.** Commands in `cmd/` may only parse arguments, call into
  concept modules, and format output. Resolution, validation, and file-manipulation logic must live
  in the concept layer.
- **Helpers must not emit UI output.** Functions that resolve, compute, or validate should return
  results (or raise exceptions). Only the calling command in `cmd/` should decide what to
  `typer.echo`. This ensures helpers remain testable without patching `typer`.
- **Extract common CLI patterns into small utilities.** Repeated micro-patterns (e.g., "check a
  precondition and exit with a message if it fails") should be captured in a named helper to avoid
  copy-paste drift.

### 7. Naming & Public API Hygiene

- **Underscore convention is binding.** A function prefixed with `_` is private to its module. It
  must never be imported by other packages. If another module needs it, either rename it (drop the
  underscore) to make it public, or provide a public wrapper.
- **`__all__` must not list private symbols.** Including `_foo` in `__all__` contradicts the naming
  convention and confuses tooling. Either make the symbol public or remove it from `__all__`.
- **Avoid shadowing builtins.** Do not name modules or imports `list`, `dir`, `type`, etc. If a
  Typer command needs a builtin name, use `@app.command(name="list")` on a differently-named function
  and file (e.g., `show.py`).
- **Consistent field naming in data models.** Related fields on a data model (e.g., Pydantic, dataclass)
  should follow a uniform naming pattern. Prefer grouping related optional fields into a nested model
  when their count grows.

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

- **Isolated test directories:** Pre-create fixture directories (e.g., `mock_install/`, `mock_cache/`)
  inside the test scope so Typer's `CliRunner` operates in isolation and never touches the host's
  home directory or real cache.

- **Test subdirectory `__init__.py`:** Every test subdirectory under `tests/` must contain an empty
  `__init__.py`. This prevents import-path collisions when two subdirectories happen to contain
  identically-named files (e.g., `conftest.py`) and keeps discovery behaviour consistent across pytest
  versions.

- **Sub-component patching:** When testing functions that perform heavy I/O (e.g., network requests,
  disk writes), patch out the I/O helpers with `mocker.patch(...)` and assert on `call_args` directly
  instead of validating filesystem side effects.

- **Fixture centralization:** Consolidate shared resources (CLI runners, cache stubs, data factories) in
  the root `tests/conftest.py`. This ensures a single source of truth for mocks across all sub-suites.

- **Defensive settings mutation:** When using a shared settings fixture (e.g., a Pydantic `Settings`
  model), always use `settings.model_copy(deep=True)` before modifying values. This prevents state
  leakage between tests.

- **Parametrization:** Prefer `@pytest.mark.parametrize` for functions with multiple edge cases (e.g.,
  URL parsing, version resolution) to reduce code bulk and improve coverage visibility.

- **Mocking interactive prompts:** To test interactive CLI flows, patch `typer.prompt` or
  `typer.confirm`:
  ```python
  mocker.patch("typer.prompt", return_value=1)  # Select second option in a menu
  ```

- **Cleanup validation:** Every function that creates transient files or directories must have an
  accompanying test verifying that those resources are removed on failure (e.g., using `shutil.rmtree`
  in a `try...except` block).

- **Patch target precision:** Patch dependencies in the module where they are consumed:
  ```python
  # Correct: Patching subprocess as seen by the consuming module
  mocker.patch("myproject.version_manager.subprocess.run")
  ```

- **Unused unpacked variables:** Suppress `RUF059` warnings by using underscores for intentionally
  ignored tuple members:
  ```python
  args, _ = mock.call_args
  ```

### 11. Function Signature Purity

- **No boolean flags that change return types.** A function must not accept a `bool` parameter
  that switches its return type (e.g., returning `Path` when `show_command=False` but `list[str]`
  when `show_command=True`). This forces callers to perform `isinstance` checks and creates
  unreachable defensive branches.
- **Split instead of branching.** When a function has two fundamentally different behaviours,
  extract the shared setup into a private helper and expose two public functions with clear,
  single-typed return values:
  ```python
  # correct — two functions with clear contracts
  def build_compile_command(base_dir: Path | None = None) -> list[str]:
      """Build the compile command list without executing it."""
      ...

  def compile_modules(base_dir: Path | None = None, verbose: bool = False) -> Path:
      """Compile modules. Returns the output directory."""
      cmd = build_compile_command(base_dir)
      ...

  # forbidden — boolean flag toggles the return type
  def compile_modules(base_dir=None, show_command=False) -> Path | list[str]:
      ...
  ```

### 12. Code Hygiene

- **No commented-out code in commits.** Dead code that is commented out (as opposed to genuine
  explanatory comments) must not be committed. It obscures intent, drifts from surrounding code
  over time, and increases cognitive load during reviews. If a feature is "optional for later",
  track it as a task or TODO issue — do not leave it as a commented block in the source.
- **No stray blank lines inside blocks.** Avoid empty lines between `except` and its handler body,
  or between `if` and its first statement. These are usually copy-paste artefacts and hurt
  readability.

### 13. Type-Safe Internal Dispatch

- **Prefer explicit attribute access over `getattr` with string keys.** When only a small, fixed
  set of attributes is ever looked up, access them directly (`self.config.module_path`) rather
  than via `getattr(self.config, attr_name)`. Direct access enables static type checking and
  makes refactoring safe.
- **Prefer `Enum` or dedicated methods over string-matching branches.** If a function uses
  `if key == "foo" ... elif key == "bar"` to select between distinct strategies, convert the key
  to an `Enum` (validated at the call site) or split the function into typed helpers:
  ```python
  # correct — enum dispatch (validated at call site)
  class SubDir(Enum):
      MODULES = auto()
      CLASSES = auto()
      LIB = auto()

  def get_project_path(self, kind: SubDir) -> Path | None: ...

  # also correct — dedicated methods
  def get_modules_path(self) -> Path | None: ...
  def get_classes_path(self) -> Path | None: ...

  # avoid — stringly-typed dispatch
  def _get_project_path(self, subdir: str) -> Path | None:
      if subdir == "modules": ...
      elif subdir == "classes": ...
  ```