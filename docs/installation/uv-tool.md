# Installation using `uv tool`

[uv](https://docs.astral.sh/uv/) is a fast, modern Python package installer and resolver. Installing `tlaplus-cli` via `uv tool` runs the application in an isolated environment while making the command globally available.

## Note on Package Name

This package is distributed on PyPI as **`tlaplus-cli`** but imports as **`tla`**. There is a separate, unrelated [`tla`](https://pypi.org/project/tla/) package on PyPI (a TLA+ parser). If you have both installed, they will conflict. In practice this is unlikely since they serve different purposes, but be aware of it.

## Dependencies

*   **Java >= 11**: Required for TLC.
*   [**uv**](docs/installation/uv-tool.md): Required for installing the tool.

## Installation

To install `tlaplus-cli` system-wide:

```bash
uv tool install tlaplus-cli
```

## Upgrading

To upgrade to the latest version:

```bash
uv tool upgrade tlaplus-cli
```

## Uninstallation

To remove `tlaplus-cli` from your system:

```bash
uv tool uninstall tlaplus-cli
```
