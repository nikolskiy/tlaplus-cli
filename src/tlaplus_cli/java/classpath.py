import os
from enum import Enum, auto
from pathlib import Path

from tlaplus_cli.config.schema import Settings
from tlaplus_cli.versioning.paths import get_modules_dir


class ResolveMode(Enum):
    """Modes for classpath resolution."""

    RUNTIME = auto()  # For 'java -cp ... tlc2.TLC' (classes first)
    COMPILE = auto()  # For 'javac -cp ...' (tool jar first, no output classes)


class SubdirType(Enum):
    """Types of project-local subdirectories."""

    MODULES = auto()
    CLASSES = auto()
    LIB = auto()


class ClasspathResolver:
    """
    Centralized component for resolving Java classpaths and system properties.
    Follows a strict Specific-to-General hierarchy: CLI > Project > Config > Global.
    """

    def __init__(
        self,
        config: Settings,
        project_root: Path | None = None,
        tool_jar: Path | None = None,
        extra_libs: list[str] | None = None,
        extra_modules: list[str] | None = None,
    ):
        """
        Initialize the resolver.

        Args:
            config: The global settings.
            project_root: The root of the TLA+ project (where .tla file is).
            tool_jar: Path to tla2tools.jar.
            extra_libs: Explicit library paths from CLI.
            extra_modules: Explicit module paths from CLI.
        """
        self.config = config
        self.project_root = project_root
        self.tool_jar = tool_jar
        self.extra_libs = extra_libs or []
        self.extra_modules = extra_modules or []

    def get_project_path(self, subdir: SubdirType) -> Path | None:
        """Helper to find a project-local directory."""
        if not self.project_root:
            return None

        # 1. Try explicit workspace config mapping
        if subdir == SubdirType.MODULES:
            path = self.project_root / self.config.workspace.modules_dir
            if path.is_dir():
                return path
        elif subdir == SubdirType.CLASSES:
            path = self.project_root / self.config.workspace.classes_dir
            if path.is_dir():
                return path

        # 2. Try direct subdir (new standard)
        subdir_name = {
            SubdirType.MODULES: "modules",
            SubdirType.CLASSES: "classes",
            SubdirType.LIB: "lib",
        }[subdir]
        path = self.project_root / subdir_name
        if path.is_dir():
            return path

        # 3. Try legacy/nested 'lib' inside modules_dir
        if subdir == SubdirType.LIB:
            path = self.project_root / self.config.workspace.modules_dir / "lib"
            if path.is_dir():
                return path

        return None

    def _resolve_paths(self, cli_paths: list[str], subdir: SubdirType, config_path: str | None) -> list[str]:  # noqa: PLR0912
        """
        Resolves a set of paths following the hierarchy.
        Deduplicates while preserving order.
        """
        raw_paths = []

        # 1. CLI Arguments
        raw_paths.extend(cli_paths)

        # 2. Project-Local
        project_path = self.get_project_path(subdir)
        if project_path:
            raw_paths.append(str(project_path.absolute()))

        # 3. Config
        if config_path:
            raw_paths.append(str(Path(config_path).absolute()))

        # 4. Managed Modules (Global Cache)
        managed_dir = get_modules_dir()
        if managed_dir.is_dir():
            # Add all subdirectories of managed_dir to raw_paths so they are expanded for JARs/TLA files
            for item in sorted(managed_dir.iterdir()):
                if item.is_dir():
                    if subdir == SubdirType.LIB:
                        mod_lib = item / "lib"
                        if mod_lib.is_dir():
                            raw_paths.append(str(mod_lib.absolute()))
                        raw_paths.append(str(item.absolute()))  # Legacy fallback
                    elif subdir == SubdirType.MODULES:
                        mod_modules = item / "modules"
                        if mod_modules.is_dir():
                            raw_paths.append(str(mod_modules.absolute()))
                        raw_paths.append(str(item.absolute()))  # Legacy fallback

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for p in raw_paths:
            # Expand directories to include JARs if it's a lib path
            path_obj = Path(p)
            if path_obj.is_dir() and subdir == SubdirType.LIB:
                for jar in sorted(path_obj.glob("*.jar")):
                    jar_abs = str(jar.absolute())
                    if jar_abs not in seen:
                        seen.add(jar_abs)
                        deduped.append(jar_abs)
            else:
                p_abs = str(path_obj.absolute())
                if p_abs not in seen:
                    seen.add(p_abs)
                    deduped.append(p_abs)

        return deduped

    def resolve(self, mode: ResolveMode) -> list[str]:
        """
        Resolve all necessary paths for the classpath based on the requested mode.
        Deduplicates results while preserving the Specific-to-General order
        and mode-specific requirements.
        """
        classpath = []

        # In RUNTIME mode, custom classes shadow everything
        if mode == ResolveMode.RUNTIME:
            # Project-local classes
            classes_dir = self.get_project_path(SubdirType.CLASSES)
            if classes_dir:
                classpath.append(str(classes_dir.absolute()))

        # Cached module classes are included as dependencies in all modes (RUNTIME & COMPILE)
        managed_dir = get_modules_dir()
        if managed_dir.is_dir():
            for item in sorted(managed_dir.iterdir()):
                if item.is_dir():
                    mod_classes = item / "classes"
                    if mod_classes.is_dir():
                        classpath.append(str(mod_classes.absolute()))

        # Tool JAR
        if self.tool_jar:
            classpath.append(str(self.tool_jar.absolute()))

        # Libraries (CLI > Project > Config)
        libs = self._resolve_paths(self.extra_libs, SubdirType.LIB, self.config.module_lib_path)
        classpath.extend(libs)

        # Final deduplication (e.g. if tool_jar is also in libs)
        seen = set()
        final_cp = []
        for p in classpath:
            if p not in seen:
                seen.add(p)
                final_cp.append(p)

        return final_cp

    def get_tla_library_property(self) -> str | None:
        """
        Resolve paths for -DTLA-Library system property.
        Deduplicates, orders, and joins multiple valid directories.
        """
        modules = self._resolve_paths(self.extra_modules, SubdirType.MODULES, self.config.module_path)
        if not modules:
            return None
        return os.pathsep.join(modules)
