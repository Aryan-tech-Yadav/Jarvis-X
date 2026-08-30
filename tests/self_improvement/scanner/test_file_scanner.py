"""Tests for file_scanner.py."""

import os
import tempfile

import pytest

from app.self_improvement.scanner.file_scanner import FileScanner, InvalidPathError


class TestFileScanner:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.scanner = FileScanner(self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_scan_empty_directory(self):
        result = self.scanner.scan()
        assert result.total_files == 0
        assert result.python_files == []

    def test_scan_python_files(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("pass\n")
        with open(os.path.join(self.tmpdir, "utils.py"), "w") as f:
            f.write("pass\n")
        result = self.scanner.scan()
        assert result.total_files == 2
        assert "main.py" in result.python_files
        assert "utils.py" in result.python_files

    def test_scan_ignores_venv(self):
        os.makedirs(os.path.join(self.tmpdir, ".venv", "lib"))
        with open(os.path.join(self.tmpdir, ".venv", "lib", "main.py"), "w") as f:
            f.write("pass\n")
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("pass\n")
        result = self.scanner.scan()
        assert result.total_files == 1
        assert "main.py" in result.python_files

    def test_scan_ignores_pycache(self):
        os.makedirs(os.path.join(self.tmpdir, "__pycache__"))
        with open(os.path.join(self.tmpdir, "__pycache__", "main.cpython-311.pyc"), "w") as f:
            f.write("pass\n")
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("pass\n")
        result = self.scanner.scan()
        assert result.total_files == 1

    def test_scan_ignores_git(self):
        os.makedirs(os.path.join(self.tmpdir, ".git", "objects"))
        with open(os.path.join(self.tmpdir, ".git", "objects", "main.py"), "w") as f:
            f.write("pass\n")
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("pass\n")
        result = self.scanner.scan()
        assert result.total_files == 1

    def test_invalid_path(self):
        with pytest.raises(InvalidPathError):
            FileScanner("/nonexistent/path")

    def test_result_to_dict(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("pass\n")
        result = self.scanner.scan()
        data = result.to_dict()
        assert "root" in data
        assert "python_files" in data
        assert "total_files" in data
