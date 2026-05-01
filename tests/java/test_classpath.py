import os

from tlaplus_cli.java.classpath import ClasspathResolver, ResolveMode, SubdirType


def test_resolve_runtime_order(base_settings, tmp_path):
    """Test that RUNTIME mode puts classes first."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    classes_dir = project_root / "classes"
    classes_dir.mkdir()

    # Mock tool jar
    tool_jar = tmp_path / "tla2tools.jar"
    tool_jar.touch()

    resolver = ClasspathResolver(base_settings, project_root=project_root, tool_jar=tool_jar)
    cp = resolver.resolve(ResolveMode.RUNTIME)

    # classes should be before tool_jar
    assert str(classes_dir.absolute()) in cp
    assert str(tool_jar.absolute()) in cp
    assert cp.index(str(classes_dir.absolute())) < cp.index(str(tool_jar.absolute()))


def test_resolve_compile_order(base_settings, tmp_path):
    """Test that COMPILE mode excludes classes and prioritizes tool jar."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    classes_dir = project_root / "classes"
    classes_dir.mkdir()

    tool_jar = tmp_path / "tla2tools.jar"
    tool_jar.touch()

    resolver = ClasspathResolver(base_settings, project_root=project_root, tool_jar=tool_jar)
    cp = resolver.resolve(ResolveMode.COMPILE)

    assert str(classes_dir.absolute()) not in cp
    assert str(tool_jar.absolute()) in cp


def test_hierarchy_priority(base_settings, tmp_path):
    """Test CLI > Project > Config hierarchy."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    project_lib = project_root / "lib"
    project_lib.mkdir()
    project_jar = project_lib / "project.jar"
    project_jar.touch()

    config_lib_path = tmp_path / "config_lib"
    config_lib_path.mkdir()
    config_jar = config_lib_path / "config.jar"
    config_jar.touch()

    base_settings.module_lib_path = str(config_lib_path)

    cli_jar = tmp_path / "cli.jar"
    cli_jar.touch()

    resolver = ClasspathResolver(base_settings, project_root=project_root, extra_libs=[str(cli_jar)])
    cp = resolver.resolve(ResolveMode.RUNTIME)

    # CLI > Project > Config
    assert str(cli_jar.absolute()) in cp
    assert str(project_jar.absolute()) in cp
    assert str(config_jar.absolute()) in cp

    assert cp.index(str(cli_jar.absolute())) < cp.index(str(project_jar.absolute()))
    assert cp.index(str(project_jar.absolute())) < cp.index(str(config_jar.absolute()))


def test_deduplication(base_settings, tmp_path):
    """Test that redundant paths are removed."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    lib_dir = project_root / "lib"
    lib_dir.mkdir()
    jar = lib_dir / "foo.jar"
    jar.touch()

    # Same jar via CLI and via Project discovery
    resolver = ClasspathResolver(base_settings, project_root=project_root, extra_libs=[str(jar)])
    cp = resolver.resolve(ResolveMode.RUNTIME)

    assert cp.count(str(jar.absolute())) == 1


def test_tla_library_property(base_settings, tmp_path):
    """Test multi-path merging for -DTLA-Library."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    project_modules = project_root / "modules"
    project_modules.mkdir()

    config_modules = tmp_path / "config_modules"
    config_modules.mkdir()
    base_settings.module_path = str(config_modules)

    cli_modules = tmp_path / "cli_modules"
    cli_modules.mkdir()

    resolver = ClasspathResolver(base_settings, project_root=project_root, extra_modules=[str(cli_modules)])
    tla_library = resolver.get_tla_library_property()

    paths = tla_library.split(os.pathsep)

    assert str(cli_modules.absolute()) in paths
    assert str(project_modules.absolute()) in paths
    assert str(config_modules.absolute()) in paths

    # Order: CLI > Project > Config
    assert paths.index(str(cli_modules.absolute())) < paths.index(str(project_modules.absolute()))
    assert paths.index(str(project_modules.absolute())) < paths.index(str(config_modules.absolute()))


def test_get_project_path(base_settings, tmp_path):
    """Test get_project_path with SubdirType."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    modules_dir = project_root / "modules"
    modules_dir.mkdir()

    classes_dir = project_root / "classes"
    classes_dir.mkdir()

    lib_dir = project_root / "lib"
    lib_dir.mkdir()

    resolver = ClasspathResolver(base_settings, project_root=project_root)

    assert resolver.get_project_path(SubdirType.MODULES) == modules_dir
    assert resolver.get_project_path(SubdirType.CLASSES) == classes_dir
    assert resolver.get_project_path(SubdirType.LIB) == lib_dir
