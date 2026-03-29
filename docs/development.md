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

### 4. Pytest Patterns & Typer Mocks

**Isolated test directories:** Pre-create fixture directories (e.g., `installed_v180`, `mock_cache`)
inside the test scope so Typer's `CliRunner` operates in isolation and never touches the host's
`~/.cache` directory.

**Sub-component patching:** When testing functions that loop over installed versions (e.g.,
`tla tlc meta sync`), patch out the heavy I/O helpers with `mocker.patch(...)` and assert on
`call_args` directly instead of validating filesystem side effects.

**Unused unpacked variables:** Suppress `RUF059` warnings by using underscores for intentionally
ignored tuple members:

```python
args, _ = mock.call_args
```