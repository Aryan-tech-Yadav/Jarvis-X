import pytest

from app.agent.file_manager import FileManager


def test_save_python_path_traversal_creates_no_outside_file(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "outside-jarvis-save-test.py"

    manager = FileManager(workspace=workspace)

    assert not outside_file.exists()

    with pytest.raises(ValueError):
        manager.save_python("../outside-jarvis-save-test.py", "print('unsafe')")

    assert not outside_file.exists()


def test_read_file_path_traversal_does_not_return_outside_content(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    outside_file = tmp_path / "outside-jarvis-read-test.txt"
    outside_file.write_text("private sentinel", encoding="utf-8")

    manager = FileManager(workspace=workspace)

    with pytest.raises(ValueError):
        manager.read_file("../outside-jarvis-read-test.txt")

    assert outside_file.read_text(encoding="utf-8") == "private sentinel"


def test_overwrite_path_traversal_preserves_outside_file(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    outside_file = tmp_path / "outside-jarvis-overwrite-test.txt"
    outside_file.write_text("original sentinel", encoding="utf-8")

    manager = FileManager(workspace=workspace)

    with pytest.raises(ValueError):
        manager.overwrite_file("../outside-jarvis-overwrite-test.txt", "tampered")

    assert outside_file.read_text(encoding="utf-8") == "original sentinel"
