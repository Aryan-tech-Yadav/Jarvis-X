"""Metrics collector for Python files.

Computes per-file metrics:
  - lines of code, blank lines, comment lines
  - classes, functions, methods, imports
  - cyclomatic complexity
  - average/max function length
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class FileMetrics:
    """Metrics for a single Python file."""

    path: str
    loc: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    classes: int = 0
    functions: int = 0
    methods: int = 0
    imports: int = 0
    complexity: int = 0
    avg_function_length: float = 0.0
    max_function_length: int = 0
    max_cyclomatic_complexity: int = 0
    decorators: int = 0
    async_functions: int = 0
    docstrings: int = 0
    global_variables: int = 0
    constants: int = 0

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "loc": self.loc,
            "blank_lines": self.blank_lines,
            "comment_lines": self.comment_lines,
            "classes": self.classes,
            "functions": self.functions,
            "methods": self.methods,
            "imports": self.imports,
            "complexity": self.complexity,
            "avg_function_length": round(self.avg_function_length, 1),
            "max_function_length": self.max_function_length,
            "max_cyclomatic_complexity": self.max_cyclomatic_complexity,
            "decorators": self.decorators,
            "async_functions": self.async_functions,
            "docstrings": self.docstrings,
            "global_variables": self.global_variables,
            "constants": self.constants,
        }

    @property
    def maintainability_score(self) -> int:
        """Rough maintainability score 0-100."""
        if self.loc == 0:
            return 100
        score = 100
        if self.loc > 800:
            score -= 30
        elif self.loc > 500:
            score -= 20
        elif self.loc > 300:
            score -= 10
        if self.complexity > 20:
            score -= 20
        elif self.complexity > 10:
            score -= 10
        if self.max_function_length > 60:
            score -= 10
        return max(0, min(100, score))


class MetricsCollector:
    """Collect metrics from parsed Python files."""

    def __init__(self):
        self._cache: Dict[str, FileMetrics] = {}

    def collect(self, path: str, content: str, file_ast=None) -> FileMetrics:
        """Collect metrics for a single file.

        Args:
            path: Relative file path.
            content: File content.
            file_ast: Optional pre-parsed FileAST.

        Returns:
            FileMetrics with computed metrics.
        """
        if path in self._cache:
            return self._cache[path]

        metrics = FileMetrics(path=path)
        lines = content.splitlines()
        metrics.loc = len(lines)

        # Count blank and comment lines
        for line in lines:
            stripped = line.strip()
            if not stripped:
                metrics.blank_lines += 1
            elif stripped.startswith("#"):
                metrics.comment_lines += 1

        # Parse AST if not provided
        tree = None
        if file_ast and file_ast.tree:
            tree = file_ast.tree
        else:
            try:
                tree = ast.parse(content, filename=path)
            except SyntaxError:
                pass

        if tree:
            metrics.classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
            metrics.functions = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
            metrics.methods = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, ast.FunctionDef) and self._is_method(n)
            )
            metrics.imports = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, (ast.Import, ast.ImportFrom))
            )
            metrics.complexity = self._compute_complexity(tree)
            metrics.decorators = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and len(n.decorator_list) > 0
            )
            metrics.async_functions = sum(1 for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef))
            metrics.docstrings = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and ast.get_docstring(n)
            )
            metrics.global_variables = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and not t.id.startswith("_") for t in n.targets)
            )
            metrics.constants = sum(
                1 for n in ast.walk(tree)
                if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id.isupper() for t in n.targets)
            )

            # Function lengths
            func_lengths = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end_line = getattr(node, "end_lineno", node.lineno)
                    length = end_line - node.lineno + 1
                    func_lengths.append(length)
            if func_lengths:
                metrics.avg_function_length = sum(func_lengths) / len(func_lengths)
                metrics.max_function_length = max(func_lengths)

            # Max cyclomatic complexity per function
            complexities = []
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexities.append(self._compute_complexity(node))
            if complexities:
                metrics.max_cyclomatic_complexity = max(complexities)

        self._cache[path] = metrics
        return metrics

    def collect_batch(self, files: Dict[str, str], file_asts: Optional[Dict[str, Any]] = None) -> Dict[str, FileMetrics]:
        """Collect metrics for multiple files.

        Args:
            files: Mapping of path to content.
            file_asts: Optional mapping of path to FileAST.

        Returns:
            Mapping of path to FileMetrics.
        """
        results = {}
        for path, content in files.items():
            ast_info = file_asts.get(path) if file_asts else None
            results[path] = self.collect(path, content, ast_info)
        return results

    @staticmethod
    def _is_method(node: ast.FunctionDef) -> bool:
        """Check if function is a method (has self/cls first arg)."""
        if not node.args.args:
            return False
        first_arg = node.args.args[0].arg
        return first_arg in ("self", "cls")

    @staticmethod
    def _compute_complexity(node: ast.AST) -> int:
        """Compute cyclomatic complexity."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                  ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                complexity += len(child.generators)
            elif isinstance(child, ast.IfExp):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
        return complexity
