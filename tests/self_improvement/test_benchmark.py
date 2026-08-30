"""Tests for benchmark.py."""

import os
import tempfile

import pytest

from app.self_improvement.benchmark import BenchmarkEngine


class TestBenchmarkEngine:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.engine = BenchmarkEngine(self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_benchmark_empty_project(self):
        result = self.engine.run_benchmark(self.tmpdir, version="test")
        assert result.version == "test"
        assert isinstance(result.quality_score, float)
        assert result.execution_time > 0

    def test_benchmark_with_files(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("def hello():\n    print('Hello')\n")
        result = self.engine.run_benchmark(self.tmpdir, version="test")
        assert result.python_files >= 1
        assert result.total_lines > 0

    def test_compare_benchmarks(self):
        before = self.engine.run_benchmark(self.tmpdir, version="before")
        after = self.engine.run_benchmark(self.tmpdir, version="after")
        comparison = self.engine.compare(before, after)
        assert "before" in comparison
        assert "after" in comparison
        assert "recommendation" in comparison
