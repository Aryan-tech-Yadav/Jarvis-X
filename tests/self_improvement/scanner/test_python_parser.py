"""Tests for python_parser.py."""

import os
import tempfile

import pytest

from app.self_improvement.scanner.python_parser import PythonParser, ParseError


class TestPythonParser:
    def setup_method(self):
        self.parser = PythonParser()

    def test_parse_simple_function(self):
        content = "def hello():\n    print('Hello')\n"
        result = self.parser.parse_file("main.py", content)
        assert len(result.functions) == 1
        assert result.functions[0].name == "hello"

    def test_parse_class_with_methods(self):
        content = """
class MyClass:
    def __init__(self):
        pass
    
    def method(self):
        pass
"""
        result = self.parser.parse_file("main.py", content)
        assert len(result.classes) == 1
        assert result.classes[0].name == "MyClass"
        assert len(result.classes[0].methods) == 2

    def test_parse_imports(self):
        content = "import os\nfrom sys import path\n"
        result = self.parser.parse_file("main.py", content)
        assert len(result.imports) == 2

    def test_parse_decorators(self):
        content = "@decorator\ndef func():\n    pass\n"
        result = self.parser.parse_file("main.py", content)
        assert "decorator" in result.decorators

    def test_parse_async_function(self):
        content = "async def async_func():\n    pass\n"
        result = self.parser.parse_file("main.py", content)
        assert len(result.async_functions) == 1
        assert result.async_functions[0].name == "async_func"

    def test_parse_invalid_syntax(self):
        with pytest.raises(ParseError):
            self.parser.parse_file("main.py", "def invalid(\n")

    def test_parse_docstring(self):
        content = '"""Module docstring."""\ndef func():\n    """Func docstring."""\n    pass\n'
        result = self.parser.parse_file("main.py", content)
        assert len(result.docstrings) >= 1

    def test_to_dict(self):
        content = "def hello():\n    pass\n"
        result = self.parser.parse_file("main.py", content)
        data = result.to_dict()
        assert "path" in data
        assert "functions" in data
        assert "classes" in data
