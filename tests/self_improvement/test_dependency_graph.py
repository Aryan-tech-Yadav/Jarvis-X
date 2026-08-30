"""Tests for dependency_graph.py."""

import os
import tempfile

import pytest

from app.self_improvement.dependency_graph import DependencyGraphBuilder


class TestDependencyGraphBuilder:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.builder = DependencyGraphBuilder(self.tmpdir)

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_build_empty_project(self):
        graph = self.builder.build()
        assert isinstance(graph.nodes, list)
        assert isinstance(graph.edges, list)
        assert isinstance(graph.cycles, list)

    def test_build_simple_project(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("import os\nimport sys\n")
        with open(os.path.join(self.tmpdir, "utils.py"), "w") as f:
            f.write("import os\n")
        graph = self.builder.build()
        assert len(graph.nodes) >= 2

    def test_detect_circular_dependency(self):
        with open(os.path.join(self.tmpdir, "a.py"), "w") as f:
            f.write("from b import foo\n")
        with open(os.path.join(self.tmpdir, "b.py"), "w") as f:
            f.write("from a import bar\n")
        graph = self.builder.build()
        assert len(graph.cycles) > 0

    def test_graph_to_dict(self):
        with open(os.path.join(self.tmpdir, "main.py"), "w") as f:
            f.write("import os\n")
        graph = self.builder.build()
        data = graph.to_dict()
        assert "nodes" in data
        assert "edges" in data
        assert "cycles" in data
