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

## Java Requirements & Verification

In order to run the TLC model checker and compile custom modules, **Java must be installed on your system** and accessible in your system's `PATH`.

The TLA+ CLI provides a command to verify that your Java environment is set up correctly and meets the tool's requirements:

```bash
tla check-java
```

When run, this command will:
1. Locate the `java` executable using your system path configuration.
2. Retrieve the currently installed Java version string using `java -version`.
3. Compare the installed Java version against the minimum required version specified in your `config.yaml` (typically Java 8 or higher).

Example output:
```text
Detected Java version: 17.0.7
Java version is compatible (>= 8).
```

If Java is not installed or does not meet the compatibility requirements, the command will exit with an error.

## Cache Management

When query commands are run or versions are installed, the CLI interacts with the GitHub API to discover available TLA+ releases and tags. To avoid hitting GitHub's API rate limits (especially when run frequently in CI/CD or development environments), a local cache mechanism is implemented.

### How the Cache Works

* **Storage Location**: The cache is saved as JSON files inside your local cache directory:
  * Path: `~/.cache/tla/github_cache_{asset_name}.json` (e.g., `github_cache_tla2tools_jar.json` for the standard toolset).
* **TTL (Time to Live)**: The local cache has a TTL of **1 hour (3600 seconds)**.
  * When fetching remote versions, the CLI inspects the file modification time (`mtime`) of the cached JSON file.
  * If the file is less than 1 hour old, the CLI loads the version metadata directly from disk without performing any network requests.
* **Fallback & Offline Mode**: 
  * If the cache has expired but the CLI cannot contact the GitHub API (e.g., due to internet connection issues or rate limit blocks), the CLI will **automatically fall back to the expired cache data** (reporting a `STALE` status) so that you can continue using the tool offline.
* **Manual Clearing**:
  * To force the CLI to refresh its remote version metadata directly from GitHub, you can clear the cache manually:
    ```bash
    tla fetch-cache clear
    ```
  * This command will delete all matching `github_cache*.json` files in your cache directory, causing the next commands to perform fresh API calls.

