# TLA+ CLI

Command-line tool for working with TLA+ specifications and the TLC model checker.

## Installation

For detailed installation instructions, please refer to:
* [Installation via uv tool](docs/installation/uv-tool.md) (Recommended)
* [Nix Flakes Installation & Development](docs/installation/nix.md)


## Usage

For detailed instructions on managing TLA+ toolset versions (`tla2tools.jar`), please refer to [Managing TLA+ Tools](docs/managing-tlaplus-tools/managing-tla2tools.md).


### Run TLC

Run the TLC model checker on a specification. This uses the currently pinned toolset version.

```bash
tla tlc <spec_name>
```

For example (runs `queue.tla`):

```bash
tla tlc queue
```

To check the currently pinned `tla2tools.jar` path and its TLC version:

```bash
tla tlc --version
```

To inspect the exact Java command that will be executed without running it:

```bash
tla tlc <spec_name> --show-command
```


### Check Java Version

```bash
tla check-java
```

### Cache Management

The CLI caches GitHub API responses for 1 hour to prevent rate limiting. To clear this cache manually:

```bash
tla fetch-cache clear
```

### Directory Layout

| Directory | Purpose | Location |
|---|---|---|
| Config | `config.yaml` | `~/.config/tla/` |
| Toolset Versions | Version dirs & `tools-pinned-version.txt` file | `~/.cache/tla/tools/` |
| API Cache | `github_cache.json` | `~/.cache/tla/` |
| Workspace | specs + modules + classes | Set via `workspace.root` in config |

