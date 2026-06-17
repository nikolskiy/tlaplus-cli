# Nix Flakes Installation & Development

The project includes a `flake.nix` that provides a packaged binary and a reproducible development shell.


## Installation

### System-Wide Installation

To install `tlaplus-cli` system-wide using Nix profile:

```bash
nix profile install github:nikolskiy/tlaplus-cli
```

### Run Ad-Hoc

To build and run the CLI without installing:

```bash
nix run github:nikolskiy/tlaplus-cli -- --help
```


## Development

If you are developing `tlaplus-cli` locally, the Nix configuration ensures a reproducible environment with the correct interpreter and dependencies.

### Test the Development Shell

To enter the isolated development environment:

```bash
nix develop
```

**What happens:**
1. Nix provides `python3.12`, `uv`, and `ruff` in your `$PATH`.
2. Environment variables are set to force `uv` to use the Nix-provided Python interpreter (`UV_PYTHON`) and prevent standalone Python downloads (`UV_PYTHON_DOWNLOADS=never`).
3. The shell automatically runs `uv sync` and sources `.venv/bin/activate`.

### Test the Package Build

To build the package locally:

```bash
nix build
```

This builds the package and produces `./result/bin/tla`. You can test the generated binary directly:

```bash
./result/bin/tla --help
```

### Dependency Mapping Reference

If you modify `pyproject.toml` dependencies, ensure they are also updated in `flake.nix`'s `dependencies` list by mapping them to their `python312Packages.*` equivalents.
