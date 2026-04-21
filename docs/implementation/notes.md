# Source Code Reorganization Plan

This document outlines the proposed restructuring of the `tlaplus_cli` source code to align its structure with the actual CLI schema and separate core domain logic from the CLI layer.

## 1. Command Structure (`cmd/`)

The `cmd/` folder is treated as the concept of providing command line calls support and will directly mirror the command line interface structure. 
- If a command has subcommands, it consists of a folder where its Typer application is initialized.
- If a command is a "leaf" (an actionable command), it is a Python file within its parent's folder. 

```
src/tlaplus_cli/cmd/
├── check_java.py       # Command: `tla check-java`
├── tlc.py              # Command: `tla tlc`
├── config/             # Group: `tla config`
│   ├── __init__.py     # (Initializes the config Typer app and mounts subcommands)
│   ├── edit.py         # Subcommand: `tla config edit`
│   └── list.py         # Subcommand: `tla config list`
├── fetch_cache/        # Group: `tla fetch-cache`
│   ├── __init__.py
│   └── clear.py        # Subcommand: `tla fetch-cache clear`
├── modules/            # Group: `tla modules`
│   ├── __init__.py
│   ├── build.py        # Subcommand: `tla modules build`
│   ├── lib.py          # Subcommand: `tla modules lib`
│   └── path.py         # Subcommand: `tla modules path`
└── tools/              # Group: `tla tools`
    ├── __init__.py
    ├── dir.py          # Subcommand: `tla tools dir`
    ├── install.py      # Subcommand: `tla tools install`
    ├── list.py         # Subcommand: `tla tools list`
    ├── path.py         # Subcommand: `tla tools path`
    ├── pin.py          # Subcommand: `tla tools pin`
    ├── uninstall.py    # Subcommand: `tla tools uninstall`
    ├── upgrade.py      # Subcommand: `tla tools upgrade`
    └── meta/           # Group: `tla tools meta`
        ├── __init__.py
        └── sync.py     # Subcommand: `tla tools meta sync`
```

## 2. Concept Folders (Core Logic)

The business logic that powers the CLI commands will be separated into top-level folders representing distinct business concepts. These folders do *not* have their own command representation but are imported and used by the commands in `cmd/`.

```
src/tlaplus_cli/
├── cache/              # Concept: Caching mechanisms (e.g. GitHub API responses)
├── config/             # Concept: Loading configurations, config path resolution, schemas (settings.py)
├── java/               # Concept: Logic for parsing Java versions, JVM validations
├── project/            # Concept: Project structure representations, file operations
├── tlc/                # Concept: Invoking the TLC checker, managing modules, compilation logic
├── versioning/         # Concept: Version resolution, downloading distros, pinning (formerly version_manager.py)
├── resources/          # Concept: Static resource management (existing)  
├── cmd/                # Concept: Providing command line calls support
└── cli.py              # Main CLI entry point. Assembles `tla` by importing apps from `cmd/`
```

## 3. Recommended Migration Strategy

To safely migrate to this unified structure, we propose the following phased approach:

1. **Phase 1: Extract Concepts**: Extract pure Python domain logic out of files like `tools_manager.py` and `build_tlc_module.py`. Move this logic into the concept folders (`cache/`, `versioning/`, `tlc/`, etc.) ensuring no CLI side effects.
2. **Phase 2: Scaffold Commands**: Create the `cmd/` hierarchy with empty `__init__.py` files and the placeholder leaf files. Set up the Typer subgroup registrations.
3. **Phase 3: Relocate Leaf Commands**: Move the decorated Typer functions from their current flat files (`config_cli.py`, `tools_manager.py`, etc.) into their respective leaf subcommands in `cmd/`. Wire them to use the logic extracted in Phase 1.
4. **Phase 4: Cleanup**: Update `src/tlaplus_cli/cli.py` to import and mount the Typer instances from `src/tlaplus_cli/cmd/*/`. Remove the now-empty, flat `.py` files from the repository.
