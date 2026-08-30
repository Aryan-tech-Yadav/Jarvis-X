"""Tests for project_scanner.py."""

import ast
import os
import tempfile

import pytest

from app.self_improvement.project_scanner import ProjectScanner, ProjectScanResult


class TestProjectScanner:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.scanner = ProjectScanner(self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_scan_empty_project(self):
        result = self.scanner.scan()
        assert isinstance(result, ProjectScanResult)
        assert result.files == 0
        assert result.functions == 0
        assert result.classes == 0

    def test_scan_simple_project(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("def hello():\n    print('Hello')\n\nclass Foo:\n    pass\n")
        result = self.scanner.scan()
        assert result.files == 1
        assert result.functions >= 1
        assert result.classes >= 1
        assert result.lines_of_code > 0

    def test_scan_detects_todo(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("# TODO: fix this\ndef hello():\n    print('Hello')\n")
        result = self.scanner.scan()
        assert result.todo >= 1

    def test_scan_detects_fixme(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("# FIXME: broken\ndef hello():\n    pass\n")
        result = self.scanner.scan()
        assert result.fixme >= 1

    def test_scan_detects_long_functions(self):
        long_func = "def hello():\n" + "\n".join([f"    x = {i}" for i in range(70)]) + "\n    return x\n"
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write(long_func)
        result = self.scanner.scan()
        assert result.long_functions >= 1

    def test_scan_detects_empty_files(self):
        with open(os.path.join(self.tmpdir, "empty.py"), "w") as f:
            f.write("")
        result = self.scanner.scan()
        assert result.empty_files >= 1

    def test_scan_skips_ignored_dirs(self):
        os.makedirs(os.path.join(self.tmpdir, ".venv", "lib"))
        with open(os.path.join(self.tmpdir, ".venv", "lib", "main.py"), "w") as f:
            f.write("def hello():\n    pass\n")
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("def hello():\n    pass\n")
        result = self.scanner.scan()
        assert result.files == 1

    def test_scan_result_to_dict(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("def hello():\n    print('Hello')\n")
        result = self.scanner.scan()
        data = result.to_dict()
        assert "project_path" in data
        assert "files" in data
        assert "functions" in data
