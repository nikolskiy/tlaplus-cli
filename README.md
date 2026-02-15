# TLA+ CLI

Command-line tool for working with TLA+ specifications and the TLC model checker.

## Installation

```bash
# Install system-wide via uv tool
uv tool install .

# Or for development
uv sync
uv run tla --version
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
  root: /path/to/your/tla-project   # or relative to cwd
  spec_dir: spec
  modules_dir: modules
  classes_dir: classes

tlc:
  java_class: tlc2.TLC

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

## Dependencies

*   **Java >= 11**: Required for TLC.
*   [**uv**](https://docs.astral.sh/uv/getting-started/installation/): For installing the tool.

## Usage

### Download TLC

```bash
# Download stable release
tla download tla

# Download nightly build
tla download tla --nightly
```

### Compile Custom Java Modules

```bash
tla build
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

Override Java options at runtime:

```bash
JAVA_OPTS="-Xmx8g" tla tlc queue
```
