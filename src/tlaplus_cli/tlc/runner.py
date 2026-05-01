import os
import subprocess
from pathlib import Path

from tlaplus_cli.config.loader import load_config
from tlaplus_cli.java import validate_java_version
from tlaplus_cli.java.classpath import ClasspathResolver, ResolveMode
from tlaplus_cli.project import find_project_root
from tlaplus_cli.tlc.compiler import get_tlc_jar_path


def resolve_spec_file(spec: str) -> tuple[Path, str]:
    """Resolve a .tla spec file from a string name.

    Returns (absolute_path, display_name).
    Raises FileNotFoundError if not found.
    """
    spec_path = Path(spec)
    candidates = [
        spec_path,
        spec_path.with_suffix(".tla"),
        spec_path.parent / "spec" / (spec_path.name + ".tla"),
    ]

    spec_file = next((c for c in candidates if c.is_file()), None)
    if not spec_file:
        msg = f"Could not find a TLA+ spec file for '{spec}'"
        raise FileNotFoundError(msg)

    return spec_file.absolute(), spec_file.name


def build_tlc_command(spec: str) -> list[str]:
    """Build the java command for running TLC."""
    config = load_config()

    jar_path = get_tlc_jar_path()
    if not jar_path.exists():
        msg = "tla2tools.jar not found. Run 'tla tools install' first."
        raise FileNotFoundError(msg)

    spec_file, _ = resolve_spec_file(spec)
    project_root = find_project_root(
        spec_file, modules_dir=config.workspace.modules_dir, classes_dir=config.workspace.classes_dir
    )

    resolver = ClasspathResolver(config, project_root=project_root, tool_jar=jar_path)
    classpath = os.pathsep.join(resolver.resolve(ResolveMode.RUNTIME))

    extra_jvm_opts: list[str] = []
    tla_library = resolver.get_tla_library_property()
    if tla_library:
        extra_jvm_opts.append(f"-DTLA-Library={tla_library}")

    return [
        "java",
        *config.java.opts,
        *extra_jvm_opts,
        "-cp",
        classpath,
        config.tlc.java_class,
        spec_file.name,
    ]


def run_tlc(spec: str) -> int:
    """Run TLC model checker on a TLA+ specification. Returns exit code."""
    config = load_config()
    validate_java_version(config.java.min_version)

    spec_file, _ = resolve_spec_file(spec)
    cmd = build_tlc_command(spec)

    try:
        result = subprocess.run(cmd, cwd=str(spec_file.parent), check=False)
    except FileNotFoundError:
        msg = "'java' not found. Please install Java."
        raise FileNotFoundError(msg) from None
    else:
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
