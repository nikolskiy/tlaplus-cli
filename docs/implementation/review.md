# Code Review — `tlaplus-cli`

> **Date:** 2026-04-21  
> **Scope:** All Python source files under `src/tlaplus_cli/`  
> **Focus areas:** try/except correctness, code block nesting, general best practices

---

## Table of Contents

- [1. Try/Except Block Issues](#1-tryexcept-block-issues)
- [2. Code Structure & Nesting](#2-code-structure--nesting)
- [3. General Best Practices](#3-general-best-practices)
- [Summary Table](#summary-table)

---

## 1. Try/Except Block Issues

### 1.1 Overly broad `except Exception` in `_fetch_from_api`

**File:** `src/tlaplus_cli/versioning/api.py`, lines 20–33

**Problem:** The entire `try` block wraps **two** separate HTTP requests and their JSON deserialization. A failure in `releases_response` cannot be distinguished from a failure in `tags_response`. Also, `except Exception` is too broad — it silently swallows programming errors (e.g., `TypeError`, `AttributeError`).

```python
# Current
try:
    params = {"per_page": per_page}
    tags_response = requests.get(tags_url, params=params, timeout=10)
    tags_response.raise_for_status()
    tags_data: list[dict[str, Any]] = tags_response.json()

    releases_response = requests.get(releases_url, params=params, timeout=10)
    releases_response.raise_for_status()
    releases_data: list[dict[str, Any]] = releases_response.json()
except Exception as e:
    typer.echo(f"⚠ Warning: Failed to fetch remote versions: {e}", err=True)
    return None
else:
    return tags_data, releases_data
```

**Recommended approach:** Narrow the exception type to `requests.RequestException` (covers connection, timeout, HTTP errors). Remove the `else` clause — since the `except` branch returns, normal flow already falls through to the return.

```python
# Recommended
def _fetch_from_api(
    tags_url: str, releases_url: str, per_page: int = 30
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
    params = {"per_page": per_page}
    try:
        tags_response = requests.get(tags_url, params=params, timeout=10)
        tags_response.raise_for_status()
        releases_response = requests.get(releases_url, params=params, timeout=10)
        releases_response.raise_for_status()
    except requests.RequestException as e:
        typer.echo(f"⚠ Warning: Failed to fetch remote versions: {e}", err=True)
        return None

    tags_data: list[dict[str, Any]] = tags_response.json()
    releases_data: list[dict[str, Any]] = releases_response.json()
    return tags_data, releases_data
```

---

### 1.2 Overly broad `except Exception` in cache TTL check

**File:** `src/tlaplus_cli/versioning/api.py`, lines 78–86

**Problem:** `except Exception` catches everything including programming errors. A simple `stat()` + time comparison can only raise `OSError`. Also, the entire cache load is wrapped unnecessarily — `load_github_cache` already has its own exception handling.

```python
# Current
try:
    mtime = cache_file.stat().st_mtime
    if time.time() - mtime < 3600:
        cached_data = _load_from_cache(cache_file)
        if cached_data is not None:
            return cached_data, FetchStatus.CACHED
except Exception as e:
    typer.echo(f"⚠ Warning: Failed to check cache age: {e}", err=True)
```

**Recommended approach:** Narrow to `OSError` and only wrap the `stat()` call.

```python
# Recommended
if cache_file.exists():
    try:
        mtime = cache_file.stat().st_mtime
    except OSError as e:
        typer.echo(f"⚠ Warning: Failed to check cache age: {e}", err=True)
    else:
        if time.time() - mtime < 3600:
            cached_data = _load_from_cache(cache_file)
            if cached_data is not None:
                return cached_data, FetchStatus.CACHED
```

---

### 1.3 Overly broad `except Exception` in `load_github_cache`

**File:** `src/tlaplus_cli/cache/github.py`, lines 10–18

**Problem:** `except Exception` catches everything. Both `json.JSONDecodeError` and `OSError` are the expected failure modes here.

```python
# Current
try:
    with cache_file.open("r") as f:
        data = json.load(f)
    return [RemoteVersion(**item) for item in data]
except Exception as e:
    typer.echo(f"⚠ Warning: Failed to read cache: {e}", err=True)
```

**Recommended approach:** Catch `(json.JSONDecodeError, OSError, KeyError, TypeError)` — the specific errors that can stem from a corrupt or incompatible cache file.

```python
# Recommended
try:
    with cache_file.open("r") as f:
        data = json.load(f)
    return [RemoteVersion(**item) for item in data]
except (json.JSONDecodeError, OSError, KeyError, TypeError) as e:
    typer.echo(f"⚠ Warning: Failed to read cache: {e}", err=True)
```

---

### 1.4 Overly broad `except Exception` in `save_github_cache`

**File:** `src/tlaplus_cli/cache/github.py`, lines 21–27

**Problem:** Same pattern — `except Exception` is too broad for an I/O operation.

```python
# Current
try:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with cache_file.open("w") as f:
        json.dump([asdict(v) for v in versions], f)
except Exception as e:
    typer.echo(f"⚠ Warning: Failed to save cache: {e}", err=True)
```

**Recommended approach:**

```python
# Recommended
try:
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with cache_file.open("w") as f:
        json.dump([asdict(v) for v in versions], f)
except OSError as e:
    typer.echo(f"⚠ Warning: Failed to save cache: {e}", err=True)
```

---

### 1.5 Overly broad `except Exception` in `write_version_metadata` (×2)

**File:** `src/tlaplus_cli/versioning/metadata.py`, lines 21–48 and 76–104

**Problem:** Two nearly identical functions (`write_version_metadata` and `write_version_metadata_from_url`) both:
1. Wrap the `subprocess.run` call in `except Exception` — should use `(subprocess.SubprocessError, OSError)`.
2. Wrap the `json.dump` call in `except Exception` — should use `OSError`.

```python
# Current (in both functions)
try:
    result = subprocess.run(...)
    ...
except Exception as e:
    typer.echo(f"⚠ Warning: Failed to extract TLC version string: {e}", err=True)

try:
    with meta_file.open("w") as f:
        json.dump(metadata, f, indent=2)
except Exception as e:
    typer.echo(f"⚠ Warning: Failed to write metadata: {e}", err=True)
```

**Recommended approach:**

```python
# Recommended
try:
    result = subprocess.run(...)
    ...
except (subprocess.SubprocessError, OSError) as e:
    typer.echo(f"⚠ Warning: Failed to extract TLC version string: {e}", err=True)

try:
    with meta_file.open("w") as f:
        json.dump(metadata, f, indent=2)
except OSError as e:
    typer.echo(f"⚠ Warning: Failed to write metadata: {e}", err=True)
```

---

### 1.6 Redundant bare `raise` in `try/except/else` block

**File:** `src/tlaplus_cli/tlc/compiler.py`, lines 46–61

**Problem:** The `except subprocess.CalledProcessError: raise` block does nothing — it catches the exception only to re-raise it unchanged. This adds visual noise and an extra nesting level. Also, the `try/except/else` pattern here puts success logic in the `else` clause, adding unnecessary indentation for no protective benefit.

```python
# Current
try:
    subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
except subprocess.CalledProcessError:
    # Re-raise with info or handle in CLI
    raise
except FileNotFoundError as err:
    msg = "'javac' not found. Ensure JDK is installed and in PATH."
    raise FileNotFoundError(msg) from err
else:
    meta_inf = classes_dir / "META-INF" / "services"
    meta_inf.mkdir(parents=True, exist_ok=True)
    service_file = meta_inf / "tlc2.overrides.ITLCOverrides"
    with service_file.open("w") as f:
        f.write(f"{config.tlc.overrides_class}\n")

    return classes_dir
```

**Recommended approach:** Remove the redundant `CalledProcessError` handler (it already propagates naturally). Drop the `else` clause — since both `except` branches re-raise, code after the `try` only runs on success.

```python
# Recommended
try:
    subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
except FileNotFoundError as err:
    msg = "'javac' not found. Ensure JDK is installed and in PATH."
    raise FileNotFoundError(msg) from err

meta_inf = classes_dir / "META-INF" / "services"
meta_inf.mkdir(parents=True, exist_ok=True)
service_file = meta_inf / "tlc2.overrides.ITLCOverrides"
with service_file.open("w") as f:
    f.write(f"{config.tlc.overrides_class}\n")

return classes_dir
```

---

### 1.7 Too many statements inside `try` in `build` command

**File:** `src/tlaplus_cli/cmd/modules/build.py`, lines 18–30

**Problem:** The three `typer.echo` calls after `compile_modules()` are inside the `try` block even though they cannot raise `FileNotFoundError` or `CalledProcessError`. This makes the error contract unclear.

```python
# Current
try:
    typer.echo("Compiling Java files ...")
    classes_dir = compile_modules(base_dir, verbose)
    typer.echo(f"Successfully compiled to {classes_dir}")
    service_file = classes_dir / "META-INF" / "services" / "tlc2.overrides.ITLCOverrides"
    typer.echo(f"Created service file at {service_file}")

except FileNotFoundError as e:
    ...
except subprocess.CalledProcessError:
    ...
```

**Recommended approach:** Only `compile_modules()` needs protection by the `try`.

```python
# Recommended
typer.echo("Compiling Java files ...")
try:
    classes_dir = compile_modules(base_dir, verbose)
except FileNotFoundError as e:
    typer.echo(f"Error: {e}", err=True)
    raise typer.Exit(1) from None
except subprocess.CalledProcessError:
    typer.echo("Compilation failed!", err=True)
    raise typer.Exit(1) from None

typer.echo(f"Successfully compiled to {classes_dir}")
service_file = classes_dir / "META-INF" / "services" / "tlc2.overrides.ITLCOverrides"
typer.echo(f"Created service file at {service_file}")
```

---

### 1.8 Too many statements inside `try` in `tlc` command

**File:** `src/tlaplus_cli/cmd/tlc.py`, lines 39–51

**Problem:** Spec-resolution logic (lines 41–44) and `typer.echo` are wrapped in a `try` that only targets `FileNotFoundError` from `run_tlc()`. The spec resolution duplicates logic that already lives inside `run_tlc()`.

```python
# Current
try:
    spec_path = Path(spec)
    candidates = [spec_path, spec_path.with_suffix(".tla"), ...]
    spec_file = next((c for c in candidates if c.is_file()), None)
    spec_name = spec_file.name if spec_file else spec

    typer.echo(f"Running TLC on {spec_name} ...")
    exit_code = run_tlc(spec)
    raise typer.Exit(exit_code)
except FileNotFoundError as e:
    typer.echo(f"Error: {e}", err=True)
    raise typer.Exit(1) from None
```

**Recommended approach:** Move spec-name resolution out of the `try` block, or better yet, make `run_tlc` return the resolved spec name along with the exit code.

```python
# Recommended
spec_path = Path(spec)
candidates = [spec_path, spec_path.with_suffix(".tla"), spec_path.parent / "spec" / (spec_path.name + ".tla")]
spec_file = next((c for c in candidates if c.is_file()), None)
spec_name = spec_file.name if spec_file else spec

typer.echo(f"Running TLC on {spec_name} ...")
try:
    exit_code = run_tlc(spec)
except FileNotFoundError as e:
    typer.echo(f"Error: {e}", err=True)
    raise typer.Exit(1) from None
raise typer.Exit(exit_code)
```

---

### 1.9 `except Exception` for download logic in `install` command

**File:** `src/tlaplus_cli/cmd/tools/install.py`, lines 29–31 and 64–66

**Problem:** Two `except Exception` handlers catch everything — including `KeyboardInterrupt` effects, `SystemExit`, etc. The download functions can raise `requests.RequestException` and `OSError`.

```python
# Current
except Exception as e:
    typer.echo(f"Error: Failed to download: {e}", err=True)
    raise typer.Exit(1) from e
```

**Recommended approach:**

```python
# Recommended
except (requests.RequestException, OSError) as e:
    typer.echo(f"Error: Failed to download: {e}", err=True)
    raise typer.Exit(1) from e
```

---

### 1.10 `except Exception` in `_migrate_legacy_pin` (×3 occurrences)

**File:** `src/tlaplus_cli/versioning/paths.py`, lines 34–63

**Problem:** Three separate `except Exception` handlers for `OSError`-type operations (rename, symlink operations, file rename).

**Recommended approach:** Replace all three with `except OSError as e:`.

---

### 1.11 `except Exception` in downloader cleanup

**File:** `src/tlaplus_cli/versioning/downloader.py`, lines 52–54 and 102–104

**Problem:** `except Exception: shutil.rmtree(…); raise` catches everything. The actual expected failures are `requests.RequestException` and `OSError`.

**Recommended approach:** Narrow to `except (requests.RequestException, OSError):` so that programming errors like `TypeError` propagate with their original traceback immediately.

---

## 2. Code Structure & Nesting

### 2.1 Dead code branch in `cli.py` root callback

**File:** `src/tlaplus_cli/cli.py`, lines 45–47

**Problem:** The `if version: pass` block at the end of `root()` is dead code. The comment says it "keeps type checker happy" but this is not needed — the `version_callback` with `is_eager=True` handles this entirely. The `version` parameter's type hint (`bool`) is sufficient.

```python
# Current
if version:
    # This branch is effectively redundant due to callback, but keeps type checker happy
    pass
```

**Recommended approach:** Remove the dead branch entirely.

```python
# Recommended
@app.callback()
def root(
    version: bool = typer.Option(
        None,
        ...
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """TLA+ CLI tool."""
    load_config()
```

---

### 2.2 Duplicated spec-resolution logic in `tlc.py` and `runner.py`

**File:** `src/tlaplus_cli/cmd/tlc.py`, lines 41–44 and `src/tlaplus_cli/tlc/runner.py`, lines 23–29

**Problem:** The spec-file candidate resolution (`spec_path`, `.tla` suffix, `spec/` subdirectory) is duplicated between the CLI command and the runner. If the logic changes, both must be updated — a maintenance risk.

**Recommended approach:** Extract a shared `resolve_spec_file(spec: str) -> Path` function and place it in `tlc/runner.py` (or a dedicated utility module). Return both the resolved `Path` and the display name, then call it from both places.

---

### 2.3 Duplicated metadata functions

**File:** `src/tlaplus_cli/versioning/metadata.py`

**Problem:** `write_version_metadata` and `write_version_metadata_from_url` have nearly identical structures: extract TLC version via subprocess, build a metadata dict, write it to JSON. The only difference is the dict keys.

**Recommended approach:** Extract a private helper for the subprocess + JSON write, and call it from both public functions:

```python
# Recommended
def _extract_tlc_version(version_dir: Path) -> str:
    """Run java to get the TLC version string."""
    try:
        result = subprocess.run(
            ["java", "-cp", "tla2tools.jar", "tlc2.TLC", "-version"],
            cwd=version_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.stdout:
            return result.stdout.strip().split("\n")[0]
    except (subprocess.SubprocessError, OSError) as e:
        typer.echo(f"⚠ Warning: Failed to extract TLC version string: {e}", err=True)
    return ""


def _write_metadata(version_dir: Path, metadata: dict[str, Any]) -> None:
    """Write metadata dict to meta-tla2tools.json."""
    meta_file = version_dir / "meta-tla2tools.json"
    try:
        with meta_file.open("w") as f:
            json.dump(metadata, f, indent=2)
    except OSError as e:
        typer.echo(f"⚠ Warning: Failed to write metadata: {e}", err=True)
```

---

### 2.4 Duplicated download progress logic

**File:** `src/tlaplus_cli/versioning/downloader.py`

**Problem:** `download_version` and `download_version_from_url` share 90% identical download+progress code. This is a DRY violation.

**Recommended approach:** Extract a `_download_jar(url: str, jar_path: Path, label: str) -> None` helper:

```python
def _download_jar(url: str, jar_path: Path, label: str) -> None:
    """Download a file with a Rich progress bar."""
    response = requests.get(url, stream=True, timeout=30, headers={"User-Agent": "tlaplus-cli"})
    response.raise_for_status()
    total = int(response.headers.get("content-length", 0))

    with Progress(...) as progress:
        task = progress.add_task(f"Downloading {label}...", total=total or None)
        with jar_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                progress.update(task, advance=len(chunk))
```

---

### 2.5 Unnecessary nesting — `install.py` URL branch

**File:** `src/tlaplus_cli/cmd/tools/install.py`, lines 21–37

**Problem:** The URL branch has a dedicated `return` at the end but uses a regular comment (`# --- end URL branch ---`) as a structural marker, which adds visual noise. The `pinned_dir` check after download duplicates the same pattern used in the non-URL branch (lines 68–71).

**Recommended approach:** Consider extracting a common `_auto_pin_if_needed(version_dir)` helper and use it in both branches to remove the duplication.

---

### 2.6 Flatten nesting in `pin.py` with early returns

**File:** `src/tlaplus_cli/cmd/tools/pin.py`, lines 25–36

**Problem:** The multi-version disambiguation logic uses `if/else` with deep nesting.

```python
# Current
if len(matching) > 1:
    ...
    if 0 <= choice < len(matching):
        target = matching[choice]
    else:
        typer.echo("Invalid choice.", err=True)
        raise typer.Exit(1)
else:
    target = matching[0]
```

**Recommended approach:** Flatten with an early exit:

```python
# Recommended
if len(matching) == 1:
    target = matching[0]
else:
    typer.echo("Multiple versions match:")
    for i, lv in enumerate(matching):
        typer.echo(f"[{i}] {lv.path.name}")
    choice = typer.prompt("Select version to pin", type=int)
    if not (0 <= choice < len(matching)):
        typer.echo("Invalid choice.", err=True)
        raise typer.Exit(1)
    target = matching[choice]
```

---

### 2.7 Mixed concerns in `_resolve_upgrade_target`

**File:** `src/tlaplus_cli/cmd/tools/upgrade.py`, lines 17–32

**Problem:** The function both resolves a target and emits user-facing messages (`typer.echo`). This violates separation of concerns — library/resolution logic should not produce UI output.

**Recommended approach:** Return a result and let the caller handle the messaging:

```python
# Recommended
def _resolve_upgrade_target(version: str | None, pinned_dir: Path | None) -> tuple[str, Path | None]:
    if version:
        local_versions = list_local_versions()
        matching = [lv for lv in local_versions if lv.name == version]
        return version, matching[0].path if matching else None

    if not pinned_dir:
        raise typer.Exit(1)  # Caller handles the message

    parts = pinned_dir.name.rsplit("-", 1)
    target_name = parts[0] if len(parts) == 2 else pinned_dir.name
    return target_name, pinned_dir
```

---

## 3. General Best Practices

### 3.1 Private symbols exported in `versioning/__init__.py`

**File:** `src/tlaplus_cli/versioning/__init__.py`, lines 30–53

**Problem:** `_migrate_legacy_pin` and `_utc_now_iso` are prefixed with `_` (indicating private), yet they are exported in `__all__`. This sends mixed signals — either they are public (remove the underscore) or private (remove them from `__all__`).

```python
# Current
__all__ = [
    ...
    "_migrate_legacy_pin",
    "_utc_now_iso",
    ...
]
```

**Recommended approach:** Remove `_migrate_legacy_pin` and `_utc_now_iso` from `__all__`. If external callers need `_utc_now_iso`, rename it to `utc_now_iso` (dropping the underscore) and update references.

---

### 3.2 Missing docstrings on several command functions

**Files:**
- `cmd/tools/install.py:install()` — no docstring
- `cmd/tools/upgrade.py:upgrade()` — no docstring
- `cmd/tools/pin.py:pin()` — no docstring
- `cmd/tools/uninstall.py:uninstall()` — no docstring
- `cmd/tools/list.py:list_versions()` — no docstring
- `cmd/tools/meta/sync.py:meta_sync()` — no docstring
- `cmd/fetch_cache/clear.py:cmd_clear_cache()` — no docstring
- `versioning/resolver.py:list_local_versions()` — no docstring

**Problem:** Typer uses docstrings as the `--help` text. Missing docstrings produce empty help descriptions for CLI commands. For library functions, missing docstrings reduce maintainability.

**Recommended approach:** Add docstrings to all public functions. For Typer commands, these double as user-facing help text.

---

### 3.3 `read_version_metadata` silently swallows all exceptions

**File:** `src/tlaplus_cli/versioning/metadata.py`, lines 59–64

**Problem:** `except Exception: return None` silently hides all errors — including `json.JSONDecodeError` which may indicate real data corruption that the user should know about.

```python
# Current
try:
    with meta_file.open("r") as f:
        data: dict[str, Any] = json.load(f)
        return data
except Exception:
    return None
```

**Recommended approach:** Narrow to expected exceptions and optionally log a warning.

```python
# Recommended
try:
    with meta_file.open("r") as f:
        return json.load(f)
except (json.JSONDecodeError, OSError):
    return None
```

---

### 3.4 Inconsistent warning message formatting

**Files:** Multiple

**Problem:** Warning emoji and format vary across files:
- `"⚠ Warning: Failed to …"` (most files)
- `"Warning: Failed to …"` (without emoji — `metadata.py`, lines 87 and 104)

**Recommended approach:** Standardize all warnings. Consider creating a small utility:

```python
# tlaplus_cli/ui.py
import typer

def warn(message: str) -> None:
    typer.echo(f"⚠ Warning: {message}", err=True)
```

---

### 3.5 `version_callback` in `tlc.py` missing blank line before function

**File:** `src/tlaplus_cli/cmd/tlc.py`, lines 23–25

**Problem:** PEP 8 requires two blank lines between top-level function definitions. There is only one blank line between `version_callback` and `tlc`.

```python
# Current
        raise typer.Exit(0)

def tlc(
```

**Recommended approach:** Add a second blank line.

---

### 3.6 `cast_str` utility is module-private but could be reused

**File:** `src/tlaplus_cli/versioning/api.py`, lines 106–107

**Problem:** Function `cast_str` is defined at the bottom of `api.py` without a docstring. Its placement after the main logic makes it easy to miss. It's also a very generic utility that might be useful elsewhere.

**Recommended approach:** Either:
1. Move it to a shared utility module, or
2. At minimum, add a docstring and move it before its first usage (above `_process_remote_versions`).

---

### 3.7 `_ensure_config` is used externally but prefixed with underscore

**File:** `src/tlaplus_cli/config/loader.py`, line 68 — defined here  
**File:** `src/tlaplus_cli/cmd/config/edit.py`, line 8 — imported and used here

**Problem:** `_ensure_config` is a private function (leading underscore convention), yet it is imported and used by the `edit` command. This creates a fragile coupling to an internal API.

**Recommended approach:** Either:
1. Rename it to `ensure_config` (make it public), or
2. Call `load_config()` instead (which already calls `_ensure_config` internally) — this would suffice for the `edit` command's purpose.

---

### 3.8 `from . import list` shadows builtin

**File:** `src/tlaplus_cli/cmd/config/__init__.py`, line 5

**Problem:** `from . import list` shadows the built-in `list` in this module's namespace. While it's currently harmless (the module doesn't use `list()`), it is a latent risk and a code smell.

**Recommended approach:** Rename the file from `list.py` to `show.py` (with command name `list` preserved via `@app.command(name="list")`), or import it with an alias: `from . import list as list_cmd`.

---

### 3.9 Schema field inconsistency: `module_path` vs. `module_lib_path`

**File:** `src/tlaplus_cli/config/schema.py`, lines 49–50

**Problem:** The field names `module_path` and `module_lib_path` are not consistent — one uses a prefix, the other doesn't preserve symmetry. Also, in `compiler.py` the access pattern is `config.module_path` vs. `config.module_lib_path`, which reads awkwardly.

```python
module_path: str | None = None
module_lib_path: str | None = None
```

**Recommended approach:** Use consistent naming. Either:
- `modules_path` / `modules_lib_path`, or
- Group them in a nested model:

```python
class ModulesConfig(BaseModel):
    path: str | None = None
    lib_path: str | None = None
```

This would change access to `config.modules.path` and `config.modules.lib_path`.

---

### 3.10 `validate_java_version` silently returns on parse failure

**File:** `src/tlaplus_cli/java/inspector.py`, lines 73–77

**Problem:** If `parse_java_version` raises `ValueError` or `IndexError`, the function silently returns without raising. This means the code continues as if Java validation passed, which could lead to confusing downstream failures.

```python
# Current
try:
    major_version = parse_java_version(version_str)
except (ValueError, IndexError):
    # Warning is handled in CLI
    return
```

**Recommended approach:** Either log a warning, or raise a clear error:

```python
# Recommended
try:
    major_version = parse_java_version(version_str)
except (ValueError, IndexError):
    typer.echo(f"⚠ Warning: Could not parse Java version string: {version_str}", err=True)
    return
```

> **Note:** The comment says "Warning is handled in CLI" — but no calling code actually handles this case. The CLI layer (`check_java.py`) catches `RuntimeError`, not a silent return.

---

### 3.11 `run_tlc` doesn't validate subprocess execution

**File:** `src/tlaplus_cli/tlc/runner.py`, line 66

**Problem:** `subprocess.run(cmd, cwd=…)` is called without `capture_output` or error handling. If `java` is not found, it will raise `FileNotFoundError` — but this is not caught anywhere in `run_tlc`. The caller (`tlc.py`) catches `FileNotFoundError`, but it's intended for spec-file-not-found errors, leading to misleading error messages.

**Recommended approach:** Handle `FileNotFoundError` explicitly for the `java` binary:

```python
# Recommended
try:
    result = subprocess.run(cmd, cwd=str(spec_file.parent))
except FileNotFoundError:
    msg = "'java' not found. Please install Java."
    raise FileNotFoundError(msg) from None
return result.returncode
```

---

## Summary Table

| # | Severity | File | Issue |
|---|----------|------|-------|
| 1.1 | 🔴 High | `versioning/api.py` | `except Exception` — narrow to `requests.RequestException` |
| 1.2 | 🟡 Medium | `versioning/api.py` | `except Exception` for `stat()` — narrow to `OSError` |
| 1.3 | 🟡 Medium | `cache/github.py` | `except Exception` for JSON/IO — narrow to specific types |
| 1.4 | 🟡 Medium | `cache/github.py` | `except Exception` for save — narrow to `OSError` |
| 1.5 | 🟡 Medium | `versioning/metadata.py` | `except Exception` ×4 — narrow to specific types |
| 1.6 | 🟡 Medium | `tlc/compiler.py` | Redundant `CalledProcessError` catch + unnecessary `else` |
| 1.7 | 🟡 Medium | `cmd/modules/build.py` | Too many statements in `try` |
| 1.8 | 🟡 Medium | `cmd/tlc.py` | Too many statements in `try` |
| 1.9 | 🔴 High | `cmd/tools/install.py` | `except Exception` for download — narrow scope |
| 1.10 | 🟡 Medium | `versioning/paths.py` | `except Exception` ×3 — narrow to `OSError` |
| 1.11 | 🟡 Medium | `versioning/downloader.py` | `except Exception` in cleanup — narrow scope |
| 2.1 | 🟢 Low | `cli.py` | Dead `if version: pass` branch |
| 2.2 | 🔴 High | `cmd/tlc.py` + `tlc/runner.py` | Duplicated spec-resolution logic |
| 2.3 | 🟡 Medium | `versioning/metadata.py` | Duplicated metadata write functions |
| 2.4 | 🟡 Medium | `versioning/downloader.py` | Duplicated download+progress code |
| 2.5 | 🟢 Low | `cmd/tools/install.py` | Duplicated auto-pin pattern |
| 2.6 | 🟢 Low | `cmd/tools/pin.py` | Nesting can be flattened |
| 2.7 | 🟢 Low | `cmd/tools/upgrade.py` | `_resolve_upgrade_target` mixes UI and logic |
| 3.1 | 🟡 Medium | `versioning/__init__.py` | Private symbols in `__all__` |
| 3.2 | 🟡 Medium | Multiple | Missing docstrings on CLI commands |
| 3.3 | 🟡 Medium | `versioning/metadata.py` | Silent `except Exception: return None` |
| 3.4 | 🟢 Low | Multiple | Inconsistent warning format |
| 3.5 | 🟢 Low | `cmd/tlc.py` | Missing PEP 8 blank line |
| 3.6 | 🟢 Low | `versioning/api.py` | `cast_str` placement and docs |
| 3.7 | 🟡 Medium | `config/loader.py` | Private `_ensure_config` used externally |
| 3.8 | 🟢 Low | `cmd/config/__init__.py` | `from . import list` shadows builtin |
| 3.9 | 🟢 Low | `config/schema.py` | Inconsistent field naming |
| 3.10 | 🟡 Medium | `java/inspector.py` | Silent return on version parse failure |
| 3.11 | 🟡 Medium | `tlc/runner.py` | Missing `FileNotFoundError` handling for `java` |

> **Legend:** 🔴 High — risks incorrect behavior or masks bugs · 🟡 Medium — harms maintainability or code clarity · 🟢 Low — style / polish
