import pytest
from unittest.mock import MagicMock, patch

from app.project.project_builder import ProjectBuilder


def make_builder():
    builder = ProjectBuilder.__new__(ProjectBuilder)
    builder.static_tester = MagicMock()
    return builder


def test_valid_template_is_static_validated(tmp_path):
    builder = make_builder()
    builder.static_tester.validate_project.return_value = (
        True, "Static validation passed"
    )
    root = tmp_path / "generated"

    result = builder._build_from_template(
        {"files": {"main.py": "print('safe')"}},
        base_path=str(root),
    )

    assert result == str(root)
    assert (root / "main.py").is_file()
    builder.static_tester.validate_project.assert_called_once_with(str(root))


def test_invalid_template_is_rejected(tmp_path):
    builder = make_builder()
    builder.static_tester.validate_project.return_value = (
        False, "Syntax/read error in main.py: invalid syntax"
    )

    with pytest.raises(ValueError, match="failed static validation"):
        builder._build_from_template(
            {"files": {"main.py": "def broken("}},
            base_path=str(tmp_path / "generated"),
        )


def test_template_path_traversal_is_rejected(tmp_path):
    builder = make_builder()
    outside = tmp_path / "outside.py"

    with pytest.raises(ValueError, match="escapes the project"):
        builder._build_from_template(
            {"files": {"../outside.py": "print('unsafe')"}},
            base_path=str(tmp_path / "generated"),
        )

    assert not outside.exists()
    builder.static_tester.validate_project.assert_not_called()


def test_invalid_template_does_not_delete_existing_project(tmp_path):
    builder = make_builder()
    root = tmp_path / "generated"
    root.mkdir()
    old_file = root / "old.txt"
    old_file.write_text("keep me", encoding="utf-8")

    with pytest.raises(ValueError, match="escapes the project"):
        builder._build_from_template(
            {"files": {"../outside.py": "print('unsafe')"}},
            base_path=str(root),
        )

    assert old_file.read_text(encoding="utf-8") == "keep me"
    builder.static_tester.validate_project.assert_not_called()


def test_template_generation_does_not_execute_generated_code(tmp_path):
    builder = make_builder()
    builder.static_tester.validate_project.return_value = (
        True, "Static validation passed"
    )

    with patch("app.project.project_runner.ProjectRunner.run") as run:
        builder._build_from_template(
            {"files": {"main.py": "print('not executed during generation')"}},
            base_path=str(tmp_path / "generated"),
        )

    run.assert_not_called()
