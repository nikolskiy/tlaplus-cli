from tlaplus_cli.project import find_project_root


def test_project_root_at_spec_dir(tmp_path):
    """Root found at spec's own directory when it contains classes/."""
    spec = tmp_path / "queue.tla"
    spec.write_text("MODULE queue\n===\n")
    (tmp_path / "classes").mkdir()
    root = find_project_root(spec, modules_dir="modules", classes_dir="classes", lib_dir="lib")
    assert root == tmp_path

def test_project_root_at_parent_of_spec_dir(tmp_path):
    """Root found one level up when spec is inside a spec/ subdirectory."""
    spec_subdir = tmp_path / "spec"
    spec_subdir.mkdir()
    spec = spec_subdir / "queue.tla"
    spec.write_text("MODULE queue\n===\n")
    (tmp_path / "classes").mkdir()
    root = find_project_root(spec, modules_dir="modules", classes_dir="classes", lib_dir="lib")
    assert root == tmp_path

def test_project_root_none_when_no_structure(tmp_path):
    """Returns None if neither spec dir nor its parent contain project directories."""
    spec = tmp_path / "spec" / "queue.tla"
    spec.parent.mkdir()
    spec.write_text("MODULE queue\n===\n")
    root = find_project_root(spec, modules_dir="modules", classes_dir="classes", lib_dir="lib")
    assert root is None

def test_project_root_detected_by_lib(tmp_path):
    """Root found based on lib/ directory even without classes/."""
    spec = tmp_path / "tests" / "queue_test.tla"
    spec.parent.mkdir()
    spec.write_text("MODULE queue_test\n===\n")
    (tmp_path / "lib").mkdir()
    root = find_project_root(spec, modules_dir="modules", classes_dir="classes", lib_dir="lib")
    assert root == tmp_path

def test_project_root_detected_by_modules(tmp_path):
    """Root found based on modules/ directory alone."""
    spec = tmp_path / "spec" / "queue.tla"
    spec.parent.mkdir()
    spec.write_text("MODULE queue\n===\n")
    (tmp_path / "modules").mkdir()
    root = find_project_root(spec, modules_dir="modules", classes_dir="classes", lib_dir="lib")
    assert root == tmp_path
