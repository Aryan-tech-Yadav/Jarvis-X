import pytest

from app.agent.file_manager import FileManager


def test_save_python_inside_workspace(tmp_path):
    manager = FileManager(workspace=tmp_path)
    saved = manager.save_python("demo/main.py", "print('hello')")

    assert (tmp_path / "demo/main.py").is_file()
    assert saved == str((tmp_path / "demo/main.py").resolve())


def test_save_python_rejects_path_traversal(tmp_path):
    manager = FileManager(workspace=tmp_path)

    with pytest.raises(ValueError):
        manager.save_python("../outside.py", "print('bad')")


def test_read_file_inside_workspace(tmp_path):
    manager = FileManager(workspace=tmp_path)
    (tmp_path / "demo.txt").write_text("hello", encoding="utf-8")

    assert manager.read_file("demo.txt") == "hello"


def test_read_file_rejects_path_traversal(tmp_path):
    manager = FileManager(workspace=tmp_path)
    outside = tmp_path.parent / "outside-jarvis-test.txt"
    outside.write_text("private", encoding="utf-8")

    try:
        with pytest.raises(ValueError):
            manager.read_file("../outside-jarvis-test.txt")
    finally:
        outside.unlink(missing_ok=True)


def test_overwrite_file_requires_existing_workspace_file(tmp_path):
    manager = FileManager(workspace=tmp_path)

    with pytest.raises(FileNotFoundError):
        manager.overwrite_file("missing.txt", "content")


def test_overwrite_file_rejects_path_traversal(tmp_path):
    manager = FileManager(workspace=tmp_path)

    with pytest.raises(ValueError):
        manager.overwrite_file("../outside.txt", "content")
