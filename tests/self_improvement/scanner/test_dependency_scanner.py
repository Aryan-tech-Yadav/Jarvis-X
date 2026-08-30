"""Tests for dependency_scanner.py."""

import os
import tempfile

import pytest

from app.self_improvement.scanner.dependency_scanner import DependencyScanner


class TestDependencyScanner:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.scanner = DependencyScanner(self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_scan_empty_project(self):
        graph = self.scanner.scan({})
        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0

    def test_scan_simple_imports(self):
        files = {
            "main.py": "import utils\n",
            "utils.py": "import os\n",
        }
        graph = self.scanner.scan(files)
        assert len(graph.edges) > 0

    def test_detect_circular_dependency(self):
        files = {
            "a.py": "from b import foo\n",
            "b.py": "from a import bar\n",
        }
        graph = self.scanner.scan(files)
        assert len(graph.cycles) > 0

    def test_no_circular_dependency(self):
        files = {
            "a.py": "import os\n",
            "b.py": "import sys\n",
        }
        graph = self.scanner.scan(files)
        assert len(graph.cycles) == 0

    def test_graph_to_dict(self):
        files = {
            "main.py": "import os\n",
        }
        graph = self.scanner.scan(files)
        data = graph.to_dict()
        assert "nodes" in data
        assert "edges" in data
        assert "cycles" in data
