"""Tests for metrics_collector.py."""

import os
import tempfile

import pytest

from app.self_improvement.scanner.metrics_collector import MetricsCollector, FileMetrics


class TestMetricsCollector:
    def setup_method(self):
        self.collector = MetricsCollector()

    def test_collect_simple_file(self):
        content = "def hello():\n    print('Hello')\n"
        metrics = self.collector.collect("main.py", content)
        assert isinstance(metrics, FileMetrics)
        assert metrics.loc == 2
        assert metrics.functions == 1

    def test_collect_file_with_class(self):
        content = "class Foo:\n    def method(self):\n        pass\n"
        metrics = self.collector.collect("main.py", content)
        assert metrics.classes == 1
        assert metrics.methods == 1

    def test_collect_complexity(self):
        content = "def test():\n    if True:\n        if True:\n            pass\n"
        metrics = self.collector.collect("main.py", content)
        assert metrics.complexity > 1

    def test_collect_imports(self):
        content = "import os\nimport sys\nfrom typing import List\n"
        metrics = self.collector.collect("main.py", content)
        assert metrics.imports == 3

    def test_collect_async_function(self):
        content = "async def async_func():\n    pass\n"
        metrics = self.collector.collect("main.py", content)
        assert metrics.async_functions == 1

    def test_collect_constants(self):
        content = "MAX_VALUE = 100\nPI = 3.14\n"
        metrics = self.collector.collect("main.py", content)
        assert metrics.constants == 2

    def test_maintainability_score(self):
        metrics = FileMetrics(path="test.py", loc=100, complexity=5)
        assert 0 <= metrics.maintainability_score <= 100

    def test_metrics_to_dict(self):
        content = "def hello():\n    pass\n"
        metrics = self.collector.collect("main.py", content)
        data = metrics.to_dict()
        assert "path" in data
        assert "loc" in data
        assert "complexity" in data
