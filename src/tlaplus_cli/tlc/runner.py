import os
import subprocess
from pathlib import Path

from tlaplus_cli.config.loader import load_config
from tlaplus_cli.java import validate_java_version
from tlaplus_cli.project import find_project_root
from tlaplus_cli.tlc.compiler import get_tlc_jar_path


def run_tlc(spec: str) -> int:
    """Run TLC model checker on a TLA+ specification. Returns exit code."""
    config = load_config()

    validate_java_version(config.java.min_version)

    jar_path = get_tlc_jar_path()
    if not jar_path.exists():
        msg = "tla2tools.jar not found. Run 'tla tools install' first."
        raise FileNotFoundError(msg)

    # Spec resolution logic
    spec_path = Path(spec)
    candidates = [spec_path, spec_path.with_suffix(".tla"), spec_path.parent / "spec" / (spec_path.name + ".tla")]

    spec_file = next((c for c in candidates if c.is_file()), None)
    if not spec_file:
        msg = f"Could not find a TLA+ spec file for '{spec}'"
        raise FileNotFoundError(msg)

    spec_file = spec_file.absolute()
    project_root = find_project_root(
        spec_file, modules_dir=config.workspace.modules_dir, classes_dir=config.workspace.classes_dir
    )

    classpath_parts = [str(jar_path)]
    extra_jvm_opts: list[str] = []

    if config.module_path:
        custom_path = Path(config.module_path)
        if custom_path.is_dir():
            classpath_parts.append(str(custom_path))
            extra_jvm_opts.append(f"-DTLA-Library={custom_path}")

    if project_root:
        classes_path = project_root / config.workspace.classes_dir
        if classes_path.is_dir():
            classpath_parts.insert(0, str(classes_path))
        lib_dir = project_root / "lib"
        if lib_dir.is_dir():
            classpath_parts.extend(str(j) for j in sorted(lib_dir.glob("*.jar")))
        modules_path = project_root / config.workspace.modules_dir
        if modules_path.is_dir():
            extra_jvm_opts.append(f"-DTLA-Library={modules_path}")

    cmd = [
        "java",
        *config.java.opts,
        *extra_jvm_opts,
        "-cp",
        os.pathsep.join(classpath_parts),
        config.tlc.java_class,
        spec_file.name,
    ]

    result = subprocess.run(cmd, cwd=str(spec_file.parent))
    return result.returncode


def get_tlc_version() -> str | None:
    """Return the first line of 'java -cp tla2tools.jar tlc2.TLC -version'."""
    config = load_config()
    jar_path = get_tlc_jar_path()
    if not jar_path.exists():
        return None

    cmd = ["java", "-cp", str(jar_path), config.tlc.java_class]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout or result.stderr
        if output:
            return output.splitlines()[0]
    except (subprocess.SubprocessError, OSError):
        pass
    return None
