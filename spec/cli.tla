--------------------------- MODULE cli ---------------------------
(*
 * TLA+ specification for the tlaplus-cli tool.
 *
 * Models the complete behavioral state space of the CLI including:
 *   - Configuration initialization (first-run vs existing)
 *   - GitHub API cache lifecycle (fresh / stale / unavailable)
 *   - Version management (install, uninstall, upgrade, pin)
 *   - TLC runner jar resolution (pinned → legacy fallback)
 *   - Module build process
 *
 * Derived from: src/tlaplus_cli/
 *)
EXTENDS Naturals, Sequences, FiniteSets, TLC

CONSTANTS
    Versions,          \* set of version names, e.g. {"v1.8.0", "v1.9.1"}
    RemoteSHAs,        \* function: version name -> SHA string
    URLs               \* set of download URLs (for URL-based install)

VARIABLES
    (* --- Filesystem state --- *)
    configExists,      \* BOOLEAN: whether config.yaml exists on disk
    installedVersions, \* set of records [name |-> ..., sha |-> ...]
    pinnedVersion,     \* a record [name |-> ..., sha |-> ...] or "none"
    legacyJarExists,   \* BOOLEAN: legacy tla2tools.jar in cache root

    (* --- GitHub cache state --- *)
    cacheState,        \* "empty" | "fresh" | "stale"
    cachedVersions,    \* set of version names stored in cache

    (* --- API availability --- *)
    apiAvailable,      \* BOOLEAN: whether GitHub API is reachable

    (* --- Java environment --- *)
    javaInstalled,     \* BOOLEAN: whether java is on PATH
    javaMajorVersion,  \* Nat: major version number of installed java

    (* --- Workspace markers --- *)
    hasModulesDir,     \* BOOLEAN: modules/ directory exists
    hasClassesDir,     \* BOOLEAN: classes/ directory exists

    (* --- Operation result tracking --- *)
    lastResult         \* "ok" | "error_*" for last operation outcome

vars == <<configExists, installedVersions, pinnedVersion, legacyJarExists,
          cacheState, cachedVersions, apiAvailable,
          javaInstalled, javaMajorVersion,
          hasModulesDir, hasClassesDir, lastResult>>

\* ----------------------------------------------------------------
\* Variable Groups for UNCHANGED simplification
\* ----------------------------------------------------------------
configVars    == <<configExists>>
versionVars   == <<installedVersions, pinnedVersion>>
legacyVars    == <<legacyJarExists>>
cacheVars     == <<cacheState, cachedVersions>>
apiVars       == <<apiAvailable>>
javaVars      == <<javaInstalled, javaMajorVersion>>
workspaceVars == <<hasModulesDir, hasClassesDir>>
stateVars     == <<configVars, versionVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars>>


MC_RemoteSHAs ==
    "v1" :> "sha_a" @@ "v2" :> "sha_b"

NoneVersion == [name |-> "none", sha |-> "none"]

(* ================================================================
   Type invariant
   ================================================================ *)
TypeOK ==
    /\ configExists \in BOOLEAN
    /\ installedVersions \subseteq [name: Versions, sha: STRING]
    /\ pinnedVersion \in [name: Versions, sha: STRING] \cup {NoneVersion}
    /\ legacyJarExists \in BOOLEAN
    /\ cacheState \in {"empty", "fresh", "stale"}
    /\ cachedVersions \subseteq Versions
    /\ apiAvailable \in BOOLEAN
    /\ javaInstalled \in BOOLEAN
    /\ javaMajorVersion \in Nat
    /\ hasModulesDir \in BOOLEAN
    /\ hasClassesDir \in BOOLEAN
    /\ lastResult \in STRING

(* ================================================================
   Helper operators
   ================================================================ *)

\* Whether a specific version is installed locally
IsInstalled(v) ==
    \E iv \in installedVersions : iv.name = v

\* Compute the set of version names that are installed
InstalledNames == {iv.name : iv \in installedVersions}

\* Whether a version is currently pinned
IsPinned(v) ==
    /\ pinnedVersion /= NoneVersion
    /\ pinnedVersion.name = v

\* Whether any jar is available (pinned or legacy)
JarAvailable ==
    \/ (pinnedVersion /= NoneVersion /\ IsInstalled(pinnedVersion.name))
    \/ legacyJarExists

\* Remote versions available based on cache and API state
AvailableRemoteVersions ==
    IF apiAvailable
    THEN Versions
    ELSE IF cacheState \in {"fresh", "stale"}
         THEN cachedVersions
         ELSE {}

\* Resolve which versions we can display in list
FetchStatus ==
    IF apiAvailable
    THEN IF cacheState = "fresh" THEN "cached" ELSE "online"
    ELSE IF cacheState \in {"fresh", "stale"} THEN "stale"
         ELSE "unavailable"

\* Java version meets minimum requirement (min_version = 11)
JavaCompatible == javaInstalled /\ javaMajorVersion >= 11

(* ================================================================
   INITIAL STATE
   The system starts in a "clean install" state.
   ================================================================ *)
Init ==
    /\ configExists = FALSE
    /\ installedVersions = {}
    /\ pinnedVersion = NoneVersion
    /\ legacyJarExists = FALSE
    /\ cacheState = "empty"
    /\ cachedVersions = {}
    /\ apiAvailable \in BOOLEAN      \* unknown at start
    /\ javaInstalled \in BOOLEAN     \* unknown at start
    /\ javaMajorVersion \in 8..21    \* representative range
    /\ hasModulesDir \in BOOLEAN
    /\ hasClassesDir \in BOOLEAN
    /\ lastResult = "init"

(* ================================================================
   ACTION: EnsureConfig
   Corresponds to: Implicit execution on any command (via load_config)
   Related code: config.py
   First command invocation triggers config copy if missing.
   ================================================================ *)
EnsureConfig ==
    /\ ~configExists
    /\ configExists' = TRUE
    /\ UNCHANGED <<versionVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars, lastResult>>

(* ================================================================
   ACTION: FetchRemoteVersions
   Corresponds to: Internal execution during tools commands (list, install, upgrade)
   Related code: version_manager.py
   Models the three-tier fetch strategy: fresh cache → API → stale cache → empty.
   ================================================================ *)
FetchRemoteVersions_CacheHit ==
    \* Cache is fresh (< 1 hour old)
    /\ cacheState = "fresh"
    /\ cachedVersions /= {}
    /\ lastResult' = "ok"
    /\ UNCHANGED stateVars

FetchRemoteVersions_ApiSuccess ==
    \* Cache miss or stale, API succeeds
    /\ cacheState /= "fresh"
    /\ apiAvailable
    /\ cacheState' = "fresh"
    /\ cachedVersions' = Versions
    /\ lastResult' = "ok"
    /\ UNCHANGED <<configVars, versionVars, legacyVars, apiVars, javaVars, workspaceVars>>

FetchRemoteVersions_StaleCache ==
    \* API fails, but stale cache exists
    /\ cacheState /= "fresh"
    /\ ~apiAvailable
    /\ cacheState = "stale"
    /\ cachedVersions /= {}
    /\ lastResult' = "ok"
    /\ UNCHANGED stateVars

FetchRemoteVersions_Unavailable ==
    \* API fails and no cache at all
    /\ ~apiAvailable
    /\ cacheState = "empty"
    /\ lastResult' = "error_unavailable"
    /\ UNCHANGED stateVars

(* ================================================================
   ACTION: InstallVersion
   Corresponds to: tla tools install <version>
   Related code: tools_manager.py
   Installs a specific remote version. Auto-pins if nothing pinned.
   ================================================================ *)
InstallVersion(v) ==
    /\ configExists                 \* config must be loaded
    /\ v \in AvailableRemoteVersions
    /\ ~IsInstalled(v)              \* not already installed (no --force)
    /\ LET newEntry == [name |-> v, sha |-> RemoteSHAs[v]]
       IN
       /\ installedVersions' = installedVersions \cup {newEntry}
       \* Auto-pin if nothing pinned
       /\ pinnedVersion' = IF pinnedVersion = NoneVersion
                           THEN newEntry
                           ELSE pinnedVersion
       /\ lastResult' = "ok"
       /\ UNCHANGED <<configVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars>>

InstallVersionForce(v) ==
    \* Force reinstall of an already-installed version
    /\ configExists
    /\ v \in AvailableRemoteVersions
    /\ IsInstalled(v)
    /\ LET newEntry == [name |-> v, sha |-> RemoteSHAs[v]]
       IN
       /\ installedVersions' = (installedVersions \ {iv \in installedVersions : iv.name = v})
                                \cup {newEntry}
       /\ pinnedVersion' = IF pinnedVersion /= NoneVersion /\ pinnedVersion.name = v
                           THEN newEntry
                           ELSE pinnedVersion
       /\ lastResult' = "ok"
       /\ UNCHANGED <<configVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars>>

InstallVersionNotFound(v) ==
    \* Version not in remote repository
    /\ configExists
    /\ v \notin AvailableRemoteVersions
    /\ lastResult' = "error_not_found"
    /\ UNCHANGED stateVars

InstallFromURL ==
    \* URL-based install branch (custom URL)
    /\ configExists
    /\ URLs /= {}
    /\ LET url == CHOOSE u \in URLs : TRUE
           newEntry == [name |-> "url_version", sha |-> "timestamp"]
       IN
       /\ installedVersions' = installedVersions \cup {newEntry}
       /\ pinnedVersion' = IF pinnedVersion = NoneVersion
                           THEN newEntry
                           ELSE pinnedVersion
       /\ lastResult' = "ok"
       /\ UNCHANGED <<configVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars>>

(* ================================================================
   ACTION: UninstallVersion
   Corresponds to: tla tools uninstall <version>
   Related code: tools_manager.py
   Removes installed version. If pinned, falls back to latest remaining.
   ================================================================ *)
UninstallVersion(v) ==
    /\ configExists
    /\ IsInstalled(v)
    /\ LET target == CHOOSE iv \in installedVersions : iv.name = v
           remaining == installedVersions \ {target}
           wasPinned == pinnedVersion /= NoneVersion /\ pinnedVersion = target
       IN
       /\ installedVersions' = remaining
       /\ \/ /\ wasPinned
             /\ \/ /\ remaining /= {}
                   /\ pinnedVersion' = CHOOSE rv \in remaining : TRUE   \* fallback to latest
                \/ /\ remaining = {}
                   /\ pinnedVersion' = NoneVersion
          \/ /\ ~wasPinned
             /\ pinnedVersion' = pinnedVersion
       /\ lastResult' = "ok"
       /\ UNCHANGED <<configVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars>>

UninstallLegacy ==
    \* tla tools uninstall default
    /\ legacyJarExists
    /\ legacyJarExists' = FALSE
    /\ lastResult' = "ok"
    /\ UNCHANGED <<configVars, versionVars, cacheVars, apiVars, javaVars, workspaceVars>>

UninstallNotInstalled(v) ==
    /\ configExists
    /\ ~IsInstalled(v)
    /\ lastResult' = "error_not_found"
    /\ UNCHANGED stateVars

(* ================================================================
   ACTION: UpgradeVersion
   Corresponds to: tla tools upgrade <version>
   Related code: tools_manager.py
   Re-downloads version if remote SHA differs. Replaces old directory.
   ================================================================ *)
UpgradeVersion(v) ==
    /\ configExists
    /\ v \in AvailableRemoteVersions
    /\ IsInstalled(v)
    /\ LET oldEntry == CHOOSE iv \in installedVersions : iv.name = v
           newSha == RemoteSHAs[v]
       IN
       /\ oldEntry.sha /= newSha    \* there IS a newer SHA
       /\ LET newEntry == [name |-> v, sha |-> newSha]
              wasPinned == pinnedVersion = oldEntry
          IN
          /\ installedVersions' = (installedVersions \ {oldEntry}) \cup {newEntry}
          /\ pinnedVersion' = IF wasPinned THEN newEntry ELSE pinnedVersion
          /\ lastResult' = "ok"
          /\ UNCHANGED <<configVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars>>

UpgradeAlreadyCurrent(v) ==
    \* Version already at latest SHA
    /\ configExists
    /\ v \in AvailableRemoteVersions
    /\ IsInstalled(v)
    /\ LET oldEntry == CHOOSE iv \in installedVersions : iv.name = v
       IN oldEntry.sha = RemoteSHAs[v]
    /\ lastResult' = "ok"
    /\ UNCHANGED stateVars

UpgradeNotInstalled(v) ==
    \* Upgrade fallback: version not local → triggers install
    /\ configExists
    /\ v \in AvailableRemoteVersions
    /\ ~IsInstalled(v)
    /\ LET newEntry == [name |-> v, sha |-> RemoteSHAs[v]]
       IN
       /\ installedVersions' = installedVersions \cup {newEntry}
       /\ pinnedVersion' = IF pinnedVersion = NoneVersion
                           THEN newEntry
                           ELSE pinnedVersion
       /\ lastResult' = "ok"
       /\ UNCHANGED <<configVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars>>

(* ================================================================
   ACTION: PinVersion
   Corresponds to: tla tools pin <version>
   Related code: tools_manager.py
   Sets the active pinned version from installed versions.
   ================================================================ *)
PinVersion(v) ==
    /\ configExists
    /\ IsInstalled(v)
    /\ LET target == CHOOSE iv \in installedVersions : iv.name = v
       IN pinnedVersion' = target
    /\ lastResult' = "ok"
    /\ UNCHANGED <<configVars, legacyVars, cacheVars, apiVars, javaVars, workspaceVars, installedVersions>>

PinVersionNotInstalled(v) ==
    /\ configExists
    /\ ~IsInstalled(v)
    /\ lastResult' = "error_not_found"
    /\ UNCHANGED stateVars

(* ================================================================
   ACTION: ClearCache
   Corresponds to: tla fetch-cache clear
   Related code: tools_manager.py
   Clears the local GitHub API cache for TLA+ tool versions.
   ================================================================ *)
ClearCache ==
    /\ cacheState /= "empty"
    /\ cacheState' = "empty"
    /\ cachedVersions' = {}
    /\ lastResult' = "ok"
    /\ UNCHANGED <<configVars, versionVars, legacyVars, apiVars, javaVars, workspaceVars>>

(* ================================================================
   ACTION: CacheExpires
   Corresponds to: Implicit environmental change
   Related code: version_manager.py
   Models the passage of time causing the GitHub API cache to go stale.
   ================================================================ *)
CacheExpires ==
    /\ cacheState = "fresh"
    /\ cacheState' = "stale"
    /\ UNCHANGED <<configVars, versionVars, legacyVars, apiVars, javaVars, workspaceVars, lastResult, cachedVersions>>

(* ================================================================
   ACTION: RunTLC
   Corresponds to: tla tlc <args>
   Related code: run_tlc.py
   Models the jar resolution fallback chain and precondition checks before running TLC.
   ================================================================ *)
RunTLC_Success ==
    \* Happy path: java ok, jar found via pinned or legacy
    /\ configExists
    /\ JavaCompatible
    /\ JarAvailable
    /\ lastResult' = "ok"
    /\ UNCHANGED stateVars

RunTLC_NoJava ==
    /\ configExists
    /\ ~javaInstalled
    /\ lastResult' = "error_no_java"
    /\ UNCHANGED stateVars

RunTLC_JavaTooOld ==
    /\ configExists
    /\ javaInstalled
    /\ javaMajorVersion < 11
    /\ lastResult' = "error_java_version"
    /\ UNCHANGED stateVars

RunTLC_NoJar ==
    /\ configExists
    /\ JavaCompatible
    /\ ~JarAvailable
    /\ lastResult' = "error_no_jar"
    /\ UNCHANGED stateVars

(* ================================================================
   ACTION: BuildModules
   Corresponds to: tla modules <subcommand>
   Related code: build_tlc_module.py
   Compiles custom Java TLC modules.
   ================================================================ *)
BuildModules_Success ==
    /\ configExists
    /\ JarAvailable
    /\ hasModulesDir
    /\ lastResult' = "ok"
    /\ hasClassesDir' = TRUE  \* classes/ created by build
    /\ UNCHANGED <<configVars, versionVars, legacyVars, cacheVars, apiVars, javaVars, hasModulesDir>>

BuildModules_NoJar ==
    /\ configExists
    /\ ~JarAvailable
    /\ lastResult' = "error_no_jar"
    /\ UNCHANGED stateVars

BuildModules_NoModulesDir ==
    /\ configExists
    /\ JarAvailable
    /\ ~hasModulesDir
    /\ lastResult' = "error_no_modules_dir"
    /\ UNCHANGED stateVars

(* ================================================================
   ACTION: CheckJava
   Corresponds to: tla check-java
   Related code: check_java.py
   Checks if Java is installed and meets the minimum version requirement.
   ================================================================ *)
CheckJava_OK ==
    /\ configExists
    /\ JavaCompatible
    /\ lastResult' = "ok"
    /\ UNCHANGED stateVars

CheckJava_Missing ==
    /\ configExists
    /\ ~javaInstalled
    /\ lastResult' = "error_no_java"
    /\ UNCHANGED stateVars

CheckJava_TooOld ==
    /\ configExists
    /\ javaInstalled
    /\ javaMajorVersion < 11
    /\ lastResult' = "error_java_version"
    /\ UNCHANGED stateVars

(* ================================================================
   ACTION: ApiToggle
   Corresponds to: External system state
   Related code: N/A
   Models the external environment changing by having the API go up or down.
   ================================================================ *)
ApiGoesDown ==
    /\ apiAvailable
    /\ apiAvailable' = FALSE
    /\ UNCHANGED <<configVars, versionVars, legacyVars, cacheVars, javaVars, workspaceVars, lastResult>>

ApiComesUp ==
    /\ ~apiAvailable
    /\ apiAvailable' = TRUE
    /\ UNCHANGED <<configVars, versionVars, legacyVars, cacheVars, javaVars, workspaceVars, lastResult>>

(* ================================================================
   NEXT STATE RELATION
   ================================================================ *)
Next ==
    (* Configuration *)
    \/ EnsureConfig

    (* Remote version fetching *)
    \/ FetchRemoteVersions_CacheHit
    \/ FetchRemoteVersions_ApiSuccess
    \/ FetchRemoteVersions_StaleCache
    \/ FetchRemoteVersions_Unavailable

    (* Install *)
    \/ \E v \in Versions :
        \/ InstallVersion(v)
        \/ InstallVersionForce(v)
        \/ InstallVersionNotFound(v)
    \/ InstallFromURL

    (* Uninstall *)
    \/ \E v \in Versions :
        \/ UninstallVersion(v)
        \/ UninstallNotInstalled(v)
    \/ UninstallLegacy

    (* Upgrade *)
    \/ \E v \in Versions :
        \/ UpgradeVersion(v)
        \/ UpgradeAlreadyCurrent(v)
        \/ UpgradeNotInstalled(v)

    (* Pin *)
    \/ \E v \in Versions :
        \/ PinVersion(v)
        \/ PinVersionNotInstalled(v)

    (* Cache management *)
    \/ ClearCache
    \/ CacheExpires

    (* TLC runner *)
    \/ RunTLC_Success
    \/ RunTLC_NoJava
    \/ RunTLC_JavaTooOld
    \/ RunTLC_NoJar

    (* Module build *)
    \/ BuildModules_Success
    \/ BuildModules_NoJar
    \/ BuildModules_NoModulesDir

    (* Java check *)
    \/ CheckJava_OK
    \/ CheckJava_Missing
    \/ CheckJava_TooOld

    (* Environment changes *)
    \/ ApiGoesDown
    \/ ApiComesUp

(* ================================================================
   SAFETY PROPERTIES
   ================================================================ *)

\* The pinned version must always be installed (or "none")
PinnedIsInstalled ==
    pinnedVersion = NoneVersion \/ \E iv \in installedVersions : iv = pinnedVersion

\* After install, at least one version is pinned (auto-pin guarantee)
AfterInstallSomethingPinned ==
    installedVersions /= {} => pinnedVersion /= NoneVersion

\* Cache state transitions are well-ordered
CacheStateValid ==
    cacheState \in {"empty", "fresh", "stale"}

(* ================================================================
   LIVENESS PROPERTIES (under fairness)
   ================================================================ *)

\* If API is available, eventually the cache becomes fresh
EventuallyFreshCache ==
    []<>apiAvailable => []<>(cacheState = "fresh")

(* ================================================================
   SPECIFICATION
   ================================================================ *)
Spec == Init /\ [][Next]_vars

FairSpec == Spec /\ WF_vars(Next) /\ SF_vars(FetchRemoteVersions_ApiSuccess)

=================================================================
