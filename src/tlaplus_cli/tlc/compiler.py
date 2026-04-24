import os
import subprocess
from pathlib import Path

from tlaplus_cli.config.loader import cache_dir, load_config, workspace_root
from tlaplus_cli.versioning import get_pinned_version_dir


def get_tlc_jar_path() -> Path:
    """Resolve the path to tla2tools.jar using the fallback chain: pinned -> legacy."""
    pinned_dir = get_pinned_version_dir()
    pinned_jar = pinned_dir / "tla2tools.jar" if pinned_dir else None
    legacy = cache_dir() / "tla2tools.jar"
    return pinned_jar if (pinned_jar and pinned_jar.exists()) else legacy


def compile_modules(base_dir: Path | None = None, verbose: bool = False) -> Path:  # noqa: PLR0912, PLR0915
    """Compile custom Java modules. Returns the classes directory path."""
    config = load_config()
    base_dir = base_dir or workspace_root()

    jar_path = get_tlc_jar_path()
    if not jar_path.exists():
        msg = "tla2tools.jar not found. Run 'tla tools install' first."
        raise FileNotFoundError(msg)

    local_modules_dir = base_dir / config.workspace.modules_dir
    classes_dir = base_dir / config.workspace.classes_dir

    custom_modules_dir = None
    if config.module_path:
        custom_modules_dir = Path(config.module_path)
        if not custom_modules_dir.exists():
            msg = f"modules directory not found: {custom_modules_dir}"
            raise FileNotFoundError(msg)

    if not config.module_path and not local_modules_dir.exists():
        msg = f"modules directory not found: {local_modules_dir}"
        raise FileNotFoundError(msg)

    lib_jars = []
    if config.module_lib_path:
        lib_dir = Path(config.module_lib_path)
        if lib_dir.is_dir():
            lib_jars.extend(sorted(lib_dir.glob("*.jar")))
    else:
        if custom_modules_dir:
            custom_lib = custom_modules_dir / "lib"
            if custom_lib.is_dir():
                lib_jars.extend(sorted(custom_lib.glob("*.jar")))
        local_lib = local_modules_dir / "lib"
        if local_lib.is_dir():
            lib_jars.extend(sorted(local_lib.glob("*.jar")))

    # Remove duplicates preserving order
    unique_jars = []
    for jar in lib_jars:
        if jar not in unique_jars:
            unique_jars.append(jar)
    lib_jars = unique_jars

    classpath = os.pathsep.join([str(jar_path)] + [str(j) for j in lib_jars])

    java_files = []
    if custom_modules_dir:
        java_files.extend(list(custom_modules_dir.rglob("*.java")))
    if local_modules_dir.exists():
        java_files.extend(list(local_modules_dir.rglob("*.java")))

    if not java_files:
        return classes_dir

    classes_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["javac", "-cp", classpath, "-d", str(classes_dir), *[str(f) for f in java_files]]

    try:
        subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
    except FileNotFoundError as err:
        msg = "'javac' not found. Ensure JDK is installed and in PATH."
        raise FileNotFoundError(msg) from err

    meta_inf = classes_dir / "META-INF" / "services"
    meta_inf.mkdir(parents=True, exist_ok=True)
    service_file = meta_inf / "tlc2.overrides.ITLCOverrides"
    with service_file.open("w") as f:
        f.write(f"{config.tlc.overrides_class}\n")

    return classes_dir
