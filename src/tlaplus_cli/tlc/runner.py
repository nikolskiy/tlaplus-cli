import contextlib
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from tlaplus_cli.config.loader import load_config
from tlaplus_cli.java import validate_java_version
from tlaplus_cli.java.classpath import ClasspathResolver, ResolveMode
from tlaplus_cli.project import find_project_root
from tlaplus_cli.tlc.compiler import get_tlc_jar_path
from tlaplus_cli.tlc.models import CheckState, ModelCheckResult
from tlaplus_cli.tlc.parser import TlcParser
from tlaplus_cli.tlc.run_cache import get_spec_run_dir
from tlaplus_cli.tlc.sany import SanyParser


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


def resolve_cfg_file(cfg: str, spec_file: Path, project_root: Path | None = None) -> tuple[Path, str]:
    """Resolve a .cfg configuration file from a string name or path.

    Returns (absolute_path, cfg_arg_for_tlc).
    Raises FileNotFoundError if not found.
    """
    cfg_path = Path(cfg)
    cfg_names: list[str] = [cfg_path.name]
    if cfg_path.suffix != ".cfg":
        cfg_names.append(cfg_path.name + ".cfg")

    candidates: list[Path] = []
    if cfg_path.is_absolute():
        candidates.append(cfg_path)
        if cfg_path.suffix != ".cfg":
            candidates.append(cfg_path.with_suffix(".cfg"))
    else:
        search_dirs: list[Path] = []
        base_parent = cfg_path.parent
        search_dirs.append(spec_file.parent / base_parent)
        search_dirs.append(Path.cwd() / base_parent)
        if project_root:
            search_dirs.append(project_root / base_parent)

        seen_dirs: set[Path] = set()
        for sdir in search_dirs:
            resolved_dir = sdir.resolve()
            if resolved_dir not in seen_dirs:
                seen_dirs.add(resolved_dir)
                for cname in cfg_names:
                    candidates.append(sdir / cname)

    cfg_file = next((c for c in candidates if c.is_file()), None)
    if not cfg_file:
        msg = f"Could not find TLC configuration file '{cfg}'"
        raise FileNotFoundError(msg)

    cfg_arg = cfg_file.name
    if project_root:
        with contextlib.suppress(ValueError):
            cfg_arg = str(cfg_file.relative_to(project_root))

    return cfg_file.absolute(), cfg_arg


def get_override_classes(classpath: list[str]) -> list[str]:
    """Inspect all classpath directories and locate override classes."""
    classes = []
    for path_str in classpath:
        path = Path(path_str)
        if path.is_dir():
            service_file = path / "META-INF" / "services" / "tlc2.overrides.ITLCOverrides"
            if service_file.is_file():
                try:
                    for raw_line in service_file.read_text(encoding="utf-8").splitlines():
                        cleaned_line = raw_line.strip()
                        if cleaned_line and not cleaned_line.startswith("#"):
                            classes.append(cleaned_line)
                except OSError:
                    pass
            elif (path / "tlc2" / "overrides" / "TLCOverrides.class").is_file():
                classes.append("tlc2.overrides.TLCOverrides")

    seen = set()
    deduped = []
    for cls in classes:
        if cls not in seen:
            seen.add(cls)
            deduped.append(cls)
    return deduped


def build_tlc_command(spec: str, cfg: str | None = None) -> list[str]:
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
    classpath_resolved = resolver.resolve(ResolveMode.RUNTIME)
    classpath = os.pathsep.join(classpath_resolved)

    extra_jvm_opts: list[str] = []
    tla_library = resolver.get_tla_library_property()
    if tla_library:
        extra_jvm_opts.append(f"-DTLA-Library={tla_library}")

    override_classes = get_override_classes(classpath_resolved)
    if override_classes:
        extra_jvm_opts.append(f"-Dtlc2.overrides.TLCOverrides={os.pathsep.join(override_classes)}")

    spec_arg = spec_file.name
    if project_root:
        with contextlib.suppress(ValueError):
            spec_arg = str(spec_file.relative_to(project_root))

    run_dir = get_spec_run_dir(spec_file)

    cmd = [
        "java",
        *config.java.opts,
        *extra_jvm_opts,
        "-cp",
        classpath,
        config.tlc.java_class,
        "-metadir",
        str(run_dir),
    ]

    if cfg:
        _, cfg_arg = resolve_cfg_file(cfg, spec_file, project_root=project_root)
        cmd.extend(["-config", cfg_arg])

    cmd.append(spec_arg)
    return cmd


def run_tlc(  # noqa: PLR0912, PLR0915
    spec: str,
    callback: Callable[[ModelCheckResult], None] | None = None,
    coverage: bool = False,
    raw: bool = False,
    cfg: str | None = None,
) -> int:
    """Run TLC model checker on a TLA+ specification. Returns exit code."""
    config = load_config()
    validate_java_version(config.java.min_version)

    spec_file, _ = resolve_spec_file(spec)
    cmd = build_tlc_command(spec, cfg=cfg)


    # Ensure tool mode is enabled for structured output (unless in raw mode)
    if not raw and "-tool" not in cmd:
        cmd.insert(-1, "-tool")

    if coverage and "-coverage" not in cmd:
        # coverage expects a number of minutes between stats, default to 1
        cmd.insert(-1, "-coverage")
        cmd.insert(-1, "1")

    project_root = find_project_root(
        spec_file, modules_dir=config.workspace.modules_dir, classes_dir=config.workspace.classes_dir
    )
    cwd = project_root if project_root else spec_file.parent

    if raw:
        try:
            with subprocess.Popen(
                cmd,
                cwd=str(cwd),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            ) as process:
                try:
                    if process.stdout:
                        for line in process.stdout:
                            sys.stdout.write(line)
                            sys.stdout.flush()
                except KeyboardInterrupt:
                    process.terminate()
                    if process.stdout:
                        for line in process.stdout:
                            sys.stdout.write(line)
                            sys.stdout.flush()
                process.wait()
                return process.returncode
        except (subprocess.SubprocessError, OSError):
            msg = "'java' not found. Please install Java."
            raise FileNotFoundError(msg) from None

    parser = TlcParser()
    sany_parser = SanyParser()

    try:
        with subprocess.Popen(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        ) as process:
            try:
                if process.stdout:
                    for line in process.stdout:
                        if line.startswith("@!@!@"):
                            parser.process_line(line)
                        else:
                            sany_parser.process_line(line)
                            # We also pass non-SANY, non-TLC-tool-mode lines to the TLC parser
                            # so they end up in output_lines
                            parser.process_line(line)

                        if callback:
                            res = parser.get_result()
                            res.sany_errors = sany_parser.get_errors()
                            callback(res)
            except KeyboardInterrupt:
                # Stop the TLC process gracefully
                process.terminate()
                # Parse remaining output if any
                if process.stdout:
                    for line in process.stdout:
                        parser.process_line(line)
                        if callback:
                            callback(parser.get_result())

                if callback:
                    res = parser.get_result()
                    res.state = CheckState.Stopped
                    callback(res)

            process.wait()
            return process.returncode
    except (subprocess.SubprocessError, OSError):
        msg = "'java' not found. Please install Java."
        raise FileNotFoundError(msg) from None


def get_tlc_version() -> str | None:
    """Return the first line of 'java -cp tla2tools.jar tlc2.TLC -version'."""
    config = load_config()
    jar_path = get_tlc_jar_path()
    if not jar_path.exists():
        return None

    cmd = ["java", "-cp", str(jar_path), config.tlc.java_class, "-version"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout or result.stderr
        if output:
            return output.splitlines()[0]
    except (subprocess.SubprocessError, OSError):
        pass
    return None
