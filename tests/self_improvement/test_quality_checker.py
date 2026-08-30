"""Tests for quality_checker.py."""

import os
import tempfile

import pytest

from app.self_improvement.quality_checker import QualityChecker, FileQualityReport


class TestQualityChecker:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.checker = QualityChecker(self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_check_simple_file(self):
        filepath = os.path.join(self.tmpdir, "main.py")
        with open(filepath, "w") as f:
            f.write("def hello():\n    print('Hello')\n")
        report = self.checker.check_file(filepath)
        assert isinstance(report, FileQualityReport)
        assert report.maintainability > 0
        assert report.complexity > 0

    def test_check_invalid_file(self):
        report = self.checker.check_file("nonexistent.py")
        assert report.risk == "high"
        assert len(report.issues) > 0

    def test_high_complexity_file(self):
        code = "def test():\n" + "    if True:\n        pass\n" * 15
        filepath = os.path.join(self.tmpdir, "complex.py")
        with open(filepath, "w") as f:
            f.write(code)
        report = self.checker.check_file(filepath)
        assert report.complexity > 10

    def test_check_project(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("def hello():\n    print('Hello')\n")
        reports = self.checker.check_project()
        assert len(reports) >= 1

    def test_report_to_dict(self):
        filepath = os.path.join(self.tmpdir, "main.py")
        with open(filepath, "w") as f:
            f.write("def hello():\n    print('Hello')\n")
        report = self.checker.check_file(filepath)
        data = report.to_dict()
        assert "path" in data
        assert "maintainability" in data
        assert "complexity" in data
