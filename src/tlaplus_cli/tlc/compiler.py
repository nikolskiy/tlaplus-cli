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


def compile_modules(base_dir: Path | None = None, verbose: bool = False) -> Path:
    """Compile custom Java modules. Returns the classes directory path."""
    config = load_config()
    base_dir = base_dir or workspace_root()

    jar_path = get_tlc_jar_path()
    if not jar_path.exists():
        msg = "tla2tools.jar not found. Run 'tla tools install' first."
        raise FileNotFoundError(msg)

    modules_dir = Path(config.module_path) if config.module_path else base_dir / config.workspace.modules_dir
    classes_dir = base_dir / config.workspace.classes_dir

    lib_dir = Path(config.module_lib_path) if config.module_lib_path else modules_dir / "lib"

    lib_jars = sorted(lib_dir.glob("*.jar")) if lib_dir.is_dir() else []
    classpath = os.pathsep.join([str(jar_path)] + [str(j) for j in lib_jars])

    if not modules_dir.exists():
        msg = f"modules directory not found: {modules_dir}"
        raise FileNotFoundError(msg)

    java_files = list(modules_dir.rglob("*.java"))
    if not java_files:
        return classes_dir

    classes_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["javac", "-cp", classpath, "-d", str(classes_dir), *[str(f) for f in java_files]]

    try:
        subprocess.run(cmd, check=True, capture_output=not verbose, text=True)
    except subprocess.CalledProcessError:
        # Re-raise with info or handle in CLI
        raise
    except FileNotFoundError as err:
        msg = "'javac' not found. Ensure JDK is installed and in PATH."
        raise FileNotFoundError(msg) from err
    else:
        meta_inf = classes_dir / "META-INF" / "services"
        meta_inf.mkdir(parents=True, exist_ok=True)
        service_file = meta_inf / "tlc2.overrides.ITLCOverrides"
        with service_file.open("w") as f:
            f.write(f"{config.tlc.overrides_class}\n")

        return classes_dir
