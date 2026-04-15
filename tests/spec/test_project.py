import pytest

from tlaplus_cli.project import find_project_root


@pytest.mark.parametrize(
    "setup_type, expected_rel_path",
    [
        ("spec_dir_has_classes", ""),
        ("parent_has_classes", ".."),
        ("none", None),
        ("detected_by_lib", ".."),
        ("detected_by_modules", ".."),
    ],
)
def test_find_project_root(tmp_path, setup_type, expected_rel_path):
    # Setup the directory structure
    spec_dir = tmp_path / "subdir"
    spec_dir.mkdir()
    spec_file = spec_dir / "test.tla"
    spec_file.write_text("MODULE test\n===\n")

    if setup_type == "spec_dir_has_classes":
        (spec_dir / "classes").mkdir()
    elif setup_type == "parent_has_classes":
        (tmp_path / "classes").mkdir()
    elif setup_type == "detected_by_lib":
        (tmp_path / "lib").mkdir()
    elif setup_type == "detected_by_modules":
        (tmp_path / "modules").mkdir()

    root = find_project_root(spec_file, modules_dir="modules", classes_dir="classes", lib_dir="lib")

    if expected_rel_path is None:
        assert root is None
    elif expected_rel_path == "":
        assert root == spec_dir
    elif expected_rel_path == "..":
        assert root == tmp_path
