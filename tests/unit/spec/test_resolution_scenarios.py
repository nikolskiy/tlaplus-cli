from pathlib import Path

import pytest

from tlaplus_cli.cli import app


@pytest.mark.parametrize(
    "scenario, spec_arg, setup_paths, expected_exit, expected_in_args, expected_in_output",
    [
        ("explicit_extension", "my_model.tla", ["my_model.tla"], 0, "my_model.tla", None),
        ("missing_extension_cwd", "my_model", ["my_model.tla"], 0, "my_model.tla", None),
        ("inside_spec_dir", "my_model", ["spec/my_model.tla"], 0, "my_model.tla", None),
        ("not_found_cwd", "missing_model", [], 1, None, "Error: Could not find a TLA+ spec file"),
        ("missing_extension_path", "subdir/my_model", ["subdir/my_model.tla"], 0, "my_model.tla", None),
        ("inside_spec_dir_path", "subdir/my_model", ["subdir/spec/my_model.tla"], 0, "my_model.tla", None),
        ("not_found_path", "subdir/missing_model", ["subdir/"], 1, None, "Error: Could not find a TLA+ spec file"),
    ],
)
def test_resolution_scenarios(
    mock_tlc_env, tmp_path, runner, scenario, spec_arg, setup_paths, expected_exit, expected_in_args, expected_in_output
):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        for path in setup_paths:
            p = Path(path)
            if path.endswith("/"):
                p.mkdir(parents=True, exist_ok=True)
            elif p.parent != Path():
                p.parent.mkdir(parents=True, exist_ok=True)

            if not path.endswith("/"):
                p.write_text(f"MODULE {p.stem}\n===\n")

        result = runner.invoke(app, ["tlc", spec_arg])

    assert result.exit_code == expected_exit
    if expected_in_args:
        args, _ = mock_tlc_env.call_args
        assert any(expected_in_args in arg for arg in args[0])
    if expected_in_output:
        assert expected_in_output in result.output
