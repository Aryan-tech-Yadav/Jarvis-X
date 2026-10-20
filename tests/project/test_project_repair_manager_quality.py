from unittest.mock import MagicMock

from app.project.project_repair_manager import ProjectRepairManager
from app.project.project_tester import ProjectTester


def setup_repair(tmp_path, response):
    project_root = tmp_path / "project"
    project_root.mkdir()

    source = project_root / "main.py"
    source.write_text("def original():\n    return 42\n", encoding="utf-8")

    manager = ProjectRepairManager.__new__(ProjectRepairManager)
    manager.ai = MagicMock()
    manager.ai.ask.return_value = response
    manager.tester = ProjectTester()
    manager.files = MagicMock()

    project = {"files": [{"name": "main.py", "type": "python"}]}
    return manager, project, project_root, source


def test_invalid_python_repair_preserves_original_file(tmp_path):
    manager, project, root, source = setup_repair(
        tmp_path, "def broken(:\n    pass\n"
    )
    original = source.read_text(encoding="utf-8")

    repaired = manager.repair(
        project, str(root), "Invalid import in main.py: missing symbol"
    )

    assert repaired == []
    assert source.read_text(encoding="utf-8") == original


def test_empty_ai_repair_preserves_original_file(tmp_path):
    manager, project, root, source = setup_repair(tmp_path, "  \n ")
    original = source.read_text(encoding="utf-8")

    repaired = manager.repair(
        project, str(root), "Invalid import in main.py: missing symbol"
    )

    assert repaired == []
    assert source.read_text(encoding="utf-8") == original


def test_non_string_ai_repair_is_rejected_safely(tmp_path):
    manager, project, root, source = setup_repair(tmp_path, None)
    original = source.read_text(encoding="utf-8")

    repaired = manager.repair(
        project, str(root), "Invalid import in main.py: missing symbol"
    )

    assert repaired == []
    assert source.read_text(encoding="utf-8") == original


def test_valid_python_repair_updates_file(tmp_path):
    manager, project, root, source = setup_repair(
        tmp_path, "def repaired():\n    return 7\n"
    )

    repaired = manager.repair(
        project, str(root), "Invalid import in main.py: missing symbol"
    )

    assert repaired == ["main.py"]
    assert source.read_text(encoding="utf-8") == (
        "def repaired():\n    return 7"
    )
