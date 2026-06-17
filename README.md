# TLA+ CLI

Command-line tool for working with TLA+ specifications and the TLC model checker.

## Project goals

1. Simplify managing TLA+ tools such as TLC, community modules, custom modules, etc.
2. Run TLA tools in a single CLI interface.
3. Manage and display the tools outputs.

## Features

* [Managing TLA+ Tools](docs/managing-tlaplus-tools/managing-tla2tools.md): Verify Java requirements, manage/pin `tla2tools.jar` versions, and handle cache settings.
* [Running TLC](docs/tlc/tlc.md): Run the TLC model checker, inspect commands, and execute model checking with custom modules.
* [Custom Java Modules](docs/java-modules-for-tlc/README.md): Compile, register, and manage custom Java operator overrides for TLC using automated CLI commands.

## Installation

For detailed installation instructions, please refer to:
* [Installation via uv tool](docs/installation/uv-tool.md)
* [Nix Flakes Installation & Development](docs/installation/nix.md)
