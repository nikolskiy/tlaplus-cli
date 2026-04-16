# TLA+ Specification: `tlaplus-cli` Tool Behavior

## Overview

The specification in [cli.tla](file:///home/denis/projects/2026/tlaplus-cli/dev/spec/cli.tla) models the **complete behavioral state space** of the `tlaplus-cli` tool — every command path, error condition, and environmental variation.

## State Variables → Source Mapping

| Variable            | Type                              | Source Module                                                                                                                                   |
| ------------------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `configExists`      | BOOLEAN                           | [config.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/config.py) — `_ensure_config()`                                    |
| `installedVersions` | Set of records                    | [version_manager.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/version_manager.py) — `list_local_versions()`             |
| `pinnedVersion`     | Record or `"none"`                | [version_manager.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/version_manager.py) — `get_pinned_version_dir()`          |
| `legacyJarExists`   | BOOLEAN                           | [run_tlc.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/run_tlc.py) — fallback jar at `cache_dir()/tla2tools.jar`         |
| `cacheState`        | `"empty"` ∣ `"fresh"` ∣ `"stale"` | [version_manager.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/version_manager.py) — `fetch_remote_versions()` TTL logic |
| `cachedVersions`    | Set of version names              | [version_manager.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/version_manager.py) — `github_cache.json`                 |
| `apiAvailable`      | BOOLEAN                           | External — GitHub API reachability                                                                                                              |
| `javaInstalled`     | BOOLEAN                           | [check_java.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/check_java.py) — `get_java_version()`                          |
| `javaMajorVersion`  | Nat                               | [check_java.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/check_java.py) — `parse_java_version()`                        |
| `hasModulesDir`     | BOOLEAN                           | [build_tlc_module.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/build_tlc_module.py) — workspace `modules/`              |
| `hasClassesDir`     | BOOLEAN                           | [build_tlc_module.py](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/build_tlc_module.py) — workspace `classes/`              |

## Actions → CLI Commands

### Config Initialization

```mermaid
graph TD
    A["EnsureConfig"]
```

### tla tools list

```mermaid
graph TD
    B1["FetchRemoteVersions_CacheHit"]
    B2["FetchRemoteVersions_ApiSuccess"]
    B3["FetchRemoteVersions_StaleCache"]
    B4["FetchRemoteVersions_Unavailable"]
```

### tla tools install

```mermaid
graph TD
    C1["InstallVersion(v)"]
    C2["InstallVersionForce(v)"]
    C3["InstallVersionNotFound(v)"]
    C4["InstallFromURL"]
```

### tla tools uninstall

```mermaid
graph TD
    D1["UninstallVersion(v)"]
    D2["UninstallLegacy"]
    D3["UninstallNotInstalled(v)"]
```

### tla tools upgrade

```mermaid
graph TD
    E1["UpgradeVersion(v)"]
    E2["UpgradeAlreadyCurrent(v)"]
    E3["UpgradeNotInstalled(v)"]
```

### tla tools pin

```mermaid
graph TD
    F1["PinVersion(v)"]
    F2["PinVersionNotInstalled(v)"]
```

### tla tlc

```mermaid
graph TD
    G1["RunTLC_Success"]
    G2["RunTLC_NoJava"]
    G3["RunTLC_JavaTooOld"]
    G4["RunTLC_NoJar"]
```

### tla modules build

```mermaid
graph TD
    H1["BuildModules_Success"]
    H2["BuildModules_NoJar"]
    H3["BuildModules_NoModulesDir"]
```

### Environment

```mermaid
graph TD
    I1["CacheExpires"]
    I2["ApiGoesDown"]
    I3["ApiComesUp"]
    I4["ClearCache"]
```

## Safety Invariants

| Invariant                     | Meaning                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `PinnedIsInstalled`           | The pinned version is always actually installed (or nothing is pinned). Prevents dangling pin references.    |
| `AfterInstallSomethingPinned` | If any version is installed, auto-pinning guarantees at least one is pinned. Users can always run `tla tlc`. |
| `CacheStateValid`             | Cache state is always one of the three valid values.                                                         |

## Liveness Property

| Property               | Meaning                                                                                                                     |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `EventuallyFreshCache` | If the API becomes available, the cache will eventually become fresh. Ensures the system doesn't get stuck with stale data. |

## Key Design Decisions

1. **Cache three-tier fallback**: The spec models the exact `fetch_remote_versions()` logic — try fresh cache → try API → fall back to stale cache → report unavailable.

2. **Auto-pin on first install**: Both `InstallVersion` and `InstallFromURL` auto-pin when `pinnedVersion = "none"`, matching the code in [tools_manager.py:118-120](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/tools_manager.py#L117-L121).

3. **Uninstall pin fallback**: When the pinned version is uninstalled, the spec models the fallback to the latest remaining version — matching [tools_manager.py:356-363](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/tools_manager.py#L356-L363).

4. **Jar resolution chain**: `RunTLC` and `BuildModules` both model the pinned→legacy fallback chain from [run_tlc.py:61-64](file:///home/denis/projects/2026/tlaplus-cli/dev/src/tlaplus_cli/run_tlc.py#L61-L64).

5. **Environment non-determinism**: `apiAvailable` and `javaInstalled` are initialized non-deterministically and can toggle during execution, modeling real-world conditions.

## Running the Model Checker

```bash
tla tlc cli
```

The [cli.cfg](file:///home/denis/projects/2026/tlaplus-cli/dev/spec/cli.cfg) uses a minimal model (2 versions) to keep the state space tractable while still covering all behavioral paths.
