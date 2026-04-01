# TLA+ CLI

Command-line tool for working with TLA+ specifications and the TLC model checker.

## Installation

Install system-wide via uv tool:

```bash
uv tool install tlaplus-cli
```

Upgrade:
```bash
uv tool upgrade tlaplus-cli
```

Uninstall:
```bash
uv tool uninstall tlaplus-cli
```

## Usage

### Managing TLC Versions

The `tla tlc` command group allows you to download and manage multiple versions of the TLC model checker directly from GitHub releases. 

List available and installed TLC versions:
```bash
tla tlc list
```

Install the latest TLC version:
```bash
tla tlc install
```

> [!TIP]
> The first version you install is automatically "pinned" as the default. Subsequent installs won't change your pin unless you manually use `tla tlc pin`.

Install a specific TLC version:
```bash
tla tlc install v1.8.0
```

Pin a specific version to be used by default:
```bash
tla tlc pin v1.8.0
```

Upgrade the pinned version (or a specific version) to a newer commit:
```bash
tla tlc upgrade
```

Show the TLC2 version string and absolute path to the pinned version's `tla2tools.jar`:
```bash
tla tlc path
```

Or for a specific version:
```bash
tla tlc path v1.8.0
```

Example output:
```text
TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)
/home/bob/.cache/tla/tlc/v1.8.0-5a47802/tla2tools.jar
```

Show the TLC versions directory and all installed version directories:
```bash
tla tlc dir
```

Example output:
```text
/home/bob/.cache/tla/tlc
  v1.7.0-abc1234
  v1.8.0-5a47802
```

Uninstall a specific version (or use 'default' to remove legacy jars):
```bash
tla tlc uninstall v1.8.0
```

> [!NOTE]
> If you uninstall the currently pinned version, the CLI will automatically "fall back" to the next best installed version (ranked by semver, then release date).

### Run TLC

Run the TLC model checker on a specification. This uses the currently pinned TLC version.

```bash
tla run <spec_name>
```

For example (runs `queue.tla`):

```bash
tla run queue
```

> **Note:** Starting from version `0.2.0`, the command structure has changed. To run a model, use `tla run <spec>`. For older versions (<0.2.0), the command was `tla tlc <spec>`.

### Compile Custom Java Modules

Note that modules are compiled using the pinned version of TLC.

Compile modules:
```bash
tla build
```

Verbose output:
```bash
tla build --verbose
```

Compiles `.java` files from `workspace/modules/` into `workspace/classes/`.

### Check Java Version

```bash
tla check-java
```

### Cache Management

The CLI caches GitHub API responses for 1 hour to prevent rate limiting. To clear this cache manually:

```bash
tla fetch-cache clear
```

## Configuration

On first run, a default config is created at:

```
~/.config/tla/config.yaml
```

Edit this file to set your workspace path and TLC options:

```yaml
tla:
  urls:
    tags: https://api.github.com/repos/tlaplus/tlaplus/tags
    releases: https://api.github.com/repos/tlaplus/tlaplus/releases

workspace:
  root: .                 # Project root (relative to CWD)
  spec_dir: spec          # Directory containing .tla files
  modules_dir: modules    # Directory containing .java files
  classes_dir: classes    # Directory for compiled .class files

tlc:
  java_class: tlc2.TLC
  overrides_class: tlc2.overrides.TLCOverrides

java:
  min_version: 11
  opts:
    - "-XX:+IgnoreUnrecognizedVMOptions"
    - "-XX:+UseParallelGC"
```

### Directory Layout

| Directory | Purpose | Location |
|---|---|---|
| Config | `config.yaml` | `~/.config/tla/` |
| TLC Versions | Version dirs & `tlc-pinned-version.txt` file | `~/.cache/tla/tlc/` |
| API Cache | `github_cache.json` | `~/.cache/tla/` |
| Workspace | specs + modules + classes | Set via `workspace.root` in config |

## Note on Package Name

This package is distributed on PyPI as **`tlaplus-cli`** but imports as **`tla`**. There is a separate, unrelated [`tla`](https://pypi.org/project/tla/) package on PyPI (a TLA+ parser). If you have both installed, they will conflict. In practice this is unlikely since they serve different purposes, but be aware of it.

## Dependencies

*   **Java >= 11**: Required for TLC.
*   [**uv**](https://docs.astral.sh/uv/getting-started/installation/): For installing the tool.
