# TLA+ CLI

Command-line tool for working with TLA+ specifications and the TLC model checker.

## Installation

Install system-wide via uv tool

```bash
uv tool install git+https://github.com/nikolskiy/tlaplus-cli
```

Upgrade:
```bash
uv tool upgrade tlaplus-cli
```

Uninstall

```bash
uv tool uninstall tlaplus-cli
```

## Usage

### Download TLC

```bash
# Download stable release
tla download

# Download nightly build
tla download --nightly
```

### Check Java Version

```bash
tla check-java
```

### Compile Custom Java Modules

```bash
tla build

# Verbose output
tla build --verbose
```

Compiles `.java` files from `workspace/modules/` into `workspace/classes/`.

### Run TLC

```bash
tla tlc <spec_name>
```

For example:

```bash
tla tlc queue
```

## Configuration

On first run, a default config is created at:

```
~/.config/tla/config.yaml
```

Edit this file to set your workspace path and TLC options:

```yaml
tla:
  jar_name: tla2tools.jar
  urls:
    stable: https://github.com/tlaplus/tlaplus/releases/latest/download/tla2tools.jar
    nightly: https://tla.msr-inria.inria.fr/tlatoolbox/ci/dist/tla2tools.jar

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
| Cache | `tla2tools.jar` | `~/.cache/tla/` |
| Workspace | specs + modules + classes | Set via `workspace.root` in config |

## Note on Package Name

This package is distributed on PyPI as **`tlaplus-cli`** but imports as **`tla`**. There is a separate, unrelated [`tla`](https://pypi.org/project/tla/) package on PyPI (a TLA+ parser). If you have both installed, they will conflict. In practice this is unlikely since they serve different purposes, but be aware of it.

## Dependencies

*   **Java >= 11**: Required for TLC.
*   [**uv**](https://docs.astral.sh/uv/getting-started/installation/): For installing the tool.
