# Managing TLA+ Tools

The `tla tools` command group allows you to download and manage multiple versions of the TLA+ toolset (`tla2tools.jar`) directly from GitHub releases.

## List Versions

To list all available and installed toolset versions:

```bash
tla tools list
```

## Install Versions

To install the latest toolset version:

```bash
tla tools install
```

> [!TIP]
> The first version you install is automatically "pinned" as the default. Subsequent installs won't change your pin unless you manually use `tla tools pin`.

To install a specific toolset version:

```bash
tla tools install v1.8.0
```

## Pin a Version

To pin a specific version to be used by default:

```bash
tla tools pin v1.8.0
```

## Upgrade Versions

To upgrade the pinned version (or a specific version) to a newer commit:

```bash
tla tools upgrade
```

> [!NOTE]
> If the target version to upgrade is not yet installed locally, the CLI will automatically download it.

## Locate Installed JARs

To show the absolute path to the pinned version's `tla2tools.jar`:

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

To show the toolset versions directory and all installed version directories:

```bash
tla tools dir
```

Example output:
```text
/home/bob/.cache/tla/tools
  v1.7.0-abc1234
  v1.8.0-5a47802
```

## Uninstall Versions

To uninstall a specific version (or use `default` to remove legacy jars):

```bash
tla tools uninstall v1.8.0
```

> [!TIP]
> Use `--all` to remove all installed tags for a specific version name without interactive prompts.

> [!NOTE]
> If you uninstall the currently pinned version, the CLI will automatically "fall back" to the next best installed version (ranked by semver, then release date).
