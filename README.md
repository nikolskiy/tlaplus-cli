# TLA+ CLI

Command-line tool for working with TLA+ specifications and the TLC model checker.

## Project Goals

1. Simplify managing TLA+ tools such as TLC, community modules, custom modules, etc.
2. Run TLA tools in a single CLI interface.
3. Manage and display the tool outputs.

## Quick Start & Usage

### 1. Toolset Management (`tla tools`)
* `tla check-java`: Verify Java installation and compatibility.
* `tla tools list`: List available and installed toolset versions (`tla2tools.jar`).
* `tla tools install [vX.Y.Z]`: Download and install a toolset version.
* `tla tools pin <version>`: Set default toolset version for TLC runs.

### 2. Model Checking (`tla tlc`)
* `tla tlc <spec>`: Execute TLC model checker on a specification.
* `tla tlc <spec> --show-command`: Inspect exact JVM command before execution.

### 3. Custom Java Modules (`tla modules`)
* `tla modules add <path>`: Compile Java operator overrides and register module in CLI cache.
* `tla modules list`: Display cached custom modules.
* `tla modules remove <name>`: Remove custom module from cache.

For complete, runnable specifications and Java module examples, see [docs/examples](docs/examples/).

## Quick Installation

### Via `uv tool`
```bash
uv tool install tlaplus-cli
```

### Via Nix Flakes
```bash
nix profile install github:nikolskiy/tlaplus-cli
```
