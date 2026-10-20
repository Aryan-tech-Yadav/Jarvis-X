from unittest.mock import MagicMock

from app.project.project_repair_manager import ProjectRepairManager


def make_manager():
    manager = ProjectRepairManager.__new__(ProjectRepairManager)
    manager.ai = MagicMock()
    manager.tester = MagicMock()
    manager.tester.test.return_value = (True, "syntax OK")
    manager.files = MagicMock()
    manager.ai.ask.return_value = "print('repaired')"
    return manager


def test_rejects_repair_path_outside_project(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()

    outside = tmp_path / "outside.py"
    outside.write_text("original", encoding="utf-8")

    manager = make_manager()
    project = {
        "files": [{"name": "../outside.py", "type": "python"}],
    }

    repaired = manager.repair(
        project,
        str(project_root),
        "Invalid import in ../outside.py: broken import",
    )

    assert repaired == []
    assert outside.read_text(encoding="utf-8") == "original"
    manager.ai.ask.assert_not_called()


def test_rejects_absolute_repair_path(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()

    outside = tmp_path / "outside.py"
    outside.write_text("original", encoding="utf-8")

    manager = make_manager()
    project = {"files": [{"name": str(outside), "type": "python"}]}

    repaired = manager.repair(
        project,
        str(project_root),
        f"Invalid import in {outside}: broken import",
    )

    assert repaired == []
    assert outside.read_text(encoding="utf-8") == "original"
    manager.ai.ask.assert_not_called()


def test_repairs_valid_nested_file_inside_project(tmp_path):
    project_root = tmp_path / "project"
    nested = project_root / "src" / "main.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("print('broken')", encoding="utf-8")

    manager = make_manager()
    project = {"files": [{"name": "src/main.py", "type": "python"}]}

    repaired = manager.repair(
        project,
        str(project_root),
        "Invalid import in src/main.py: missing local symbol",
    )

    assert repaired == ["src/main.py"]
    assert nested.read_text(encoding="utf-8") == "print('repaired')"
    manager.ai.ask.assert_called_once()
