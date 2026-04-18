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

### Managing TLA+ Tools

The `tla tools` command group allows you to download and manage multiple versions of the TLA+ toolset (TLC, SANY, TLATeX) directly from GitHub releases. 

List available and installed toolset versions:
```bash
tla tools list
```

Install the latest toolset version:
```bash
tla tools install
```

> [!TIP]
> The first version you install is automatically "pinned" as the default. Subsequent installs won't change your pin unless you manually use `tla tools pin`.

Install a specific toolset version:
```bash
tla tools install v1.8.0
```

Pin a specific version to be used by default:
```bash
tla tools pin v1.8.0
```

Upgrade the pinned version (or a specific version) to a newer commit:
```bash
tla tools upgrade
```

> [!NOTE]
> If the target version to upgrade is not yet installed locally, the CLI will automatically download it.

Show the absolute path to the pinned version's `tla2tools.jar`:
```bash
tla tools path
```

Or for a specific version:
```bash
tla tools path v1.8.0
```

Example output:
```text
/home/bob/.cache/tla/tools/v1.8.0-5a47802/tla2tools.jar
```

Show the toolset versions directory and all installed version directories:
```bash
tla tools dir
```

Example output:
```text
/home/bob/.cache/tla/tools
  v1.7.0-abc1234
  v1.8.0-5a47802
```

Uninstall a specific version (or use 'default' to remove legacy jars):
```bash
tla tools uninstall v1.8.0
```

> [!TIP]
> Use `--all` to remove all installed tags for a specific version name without interactive prompts.

> [!NOTE]
> If you uninstall the currently pinned version, the CLI will automatically "fall back" to the next best installed version (ranked by semver, then release date).

### Run TLC

Run the TLC model checker on a specification. This uses the currently pinned toolset version.

```bash
tla tlc <spec_name>
```

For example (runs `queue.tla`):

```bash
tla tlc queue
```

#### Project-Aware Execution

The CLI intelligently resolves the specification file and its project structure. It will check the following locations:
1.  `<spec_name>` (if it's a direct path to a file, e.g., `models/my_model.tla`)
2.  `<spec_name>.tla`
3.  `spec/<spec_name>.tla` (checks an inner `spec/` folder relative to the spec's location)

Furthermore, it automatically discovers the **project root** by looking for `modules/`, `classes/`, or `lib/` directories adjacent to the spec file or its parent. When a project root is found:
- The project's `classes/` directory is added to the Java classpath.
- Any `*.jar` files found in the project's `lib/` directory are added to the Java classpath.
- The `-DTLA-Library` system property is set to the project's `modules/` directory, allowing TLC to find your custom Java overrides.

To check the currently pinned `tla2tools.jar` path and its TLC version:

```bash
tla tlc --version
```

### Compile Custom Java Modules

Java modules (overrides) are compiled using the pinned version of the toolset.

Compile modules in the current project:
```bash
tla modules build
```

Compile modules in a specific project path:
```bash
tla modules build path/to/project
```

Configure a persistent custom modules path:
```bash
tla modules path /path/to/custom/modules
```

> [!TIP]
> Setting a persistent `module_path` allows `tla modules build` and `tla tlc` to resolve your Java overrides regardless of where the commands are executed.

Verbose output:
```bash
tla modules build --verbose
```

The build command:
1. Resolves the project root (defaults to `workspace.root` from config).
2. Includes `lib/*.jar` files from the project root in the `javac` classpath.
3. Compiles `.java` files from the project's `modules/` directory into its `classes/` directory.
4. Generates the necessary Java service provider configuration for TLC overrides.

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

module_path: null         # (Optional) Persistent custom modules path

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
| Toolset Versions | Version dirs & `tools-pinned-version.txt` file | `~/.cache/tla/tools/` |
| API Cache | `github_cache.json` | `~/.cache/tla/` |
| Workspace | specs + modules + classes | Set via `workspace.root` in config |

## Note on Package Name

This package is distributed on PyPI as **`tlaplus-cli`** but imports as **`tla`**. There is a separate, unrelated [`tla`](https://pypi.org/project/tla/) package on PyPI (a TLA+ parser). If you have both installed, they will conflict. In practice this is unlikely since they serve different purposes, but be aware of it.

## Dependencies

*   **Java >= 11**: Required for TLC.
*   [**uv**](https://docs.astral.sh/uv/getting-started/installation/): For installing the tool.
