"""Project scanner for self-improvement.

Scans the Jarvis-X codebase and produces structured metrics:
  - files, classes, functions, lines of code
  - duplicates, TODOs, FIXMEs
  - long functions, empty files, dead files
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class ProjectScanResult:
    """Structured scan result."""

    project_path: str
    scanned_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    files: int = 0
    classes: int = 0
    functions: int = 0
    lines_of_code: int = 0
    todo: int = 0
    fixme: int = 0
    duplicates: int = 0
    dead_code: int = 0
    long_functions: int = 0
    empty_files: int = 0
    dead_files: int = 0
    python_files: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "scanned_at": self.scanned_at,
            "files": self.files,
            "classes": self.classes,
            "functions": self.functions,
            "lines_of_code": self.lines_of_code,
            "todo": self.todo,
            "fixme": self.fixme,
            "duplicates": self.duplicates,
            "dead_code": self.dead_code,
            "long_functions": self.long_functions,
            "empty_files": self.empty_files,
            "dead_files": self.dead_files,
            "python_files": list(self.python_files),
            "details": dict(self.details),
        }


class ProjectScanner:
    """Scan a Python project and extract structural metrics."""

    def __init__(self, project_path: str = "."):
        self.project_path = os.path.abspath(project_path)
        self.ignored_dirs = {
            ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
            "node_modules", "dist", "build", "workspace", ".sandboxes",
        }

    def scan(self) -> ProjectScanResult:
        """Run full project scan."""
        result = ProjectScanResult(project_path=self.project_path)
        result.python_files = self._collect_python_files()
        result.files = len(result.python_files)

        parsed = self._parse_files(result.python_files)

        # Count AST nodes
        for rel_path, (tree, content) in parsed.items():
            result.classes += sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            result.functions += sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
            result.lines_of_code += len(content.splitlines())

            # TODO/FIXME
            for line in content.splitlines():
                stripped = line.strip()
                if "TODO" in stripped:
                    result.todo += 1
                if "FIXME" in stripped:
                    result.fixme += 1

            # Long functions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end_line = getattr(node, "end_lineno", node.lineno)
                    if end_line - node.lineno + 1 > 60:
                        result.long_functions += 1

        # Duplicates
        result.duplicates = self._count_duplicates(parsed)

        # Empty files
        result.empty_files = self._count_empty_files(parsed)

        # Dead files
        result.dead_files = self._count_dead_files(parsed)

        # Dead code (uncalled private functions)
        result.dead_code = self._count_dead_code(parsed)

        result.details = {
            "avg_lines_per_file": round(result.lines_of_code / max(1, result.files), 1),
            "avg_functions_per_file": round(result.functions / max(1, result.files), 1),
            "avg_classes_per_file": round(result.classes / max(1, result.files), 1),
            "todo_fixme_ratio": round((result.todo + result.fixme) / max(1, result.files), 2),
        }

        return result

    def _collect_python_files(self) -> List[str]:
        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            for filename in filenames:
                if filename.endswith(".py"):
                    filepath = os.path.join(root, filename)
                    rel_path = os.path.relpath(filepath, self.project_path)
                    files.append(rel_path)
        return sorted(files)

    def _parse_files(self, python_files: List[str]) -> Dict[str, tuple]:
        parsed = {}
        for rel_path in python_files:
            filepath = os.path.join(self.project_path, rel_path)
            try:
                with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                tree = ast.parse(content, filename=rel_path)
                parsed[rel_path] = (tree, content)
            except (OSError, SyntaxError, UnicodeDecodeError):
                continue
        return parsed

    def _count_duplicates(self, parsed: Dict[str, tuple]) -> int:
        blocks: Dict[str, List[str]] = {}
        min_lines = 4
        for rel_path, (_, content) in parsed.items():
            lines = [line.strip() for line in content.splitlines()]
            for i in range(len(lines) - min_lines + 1):
                chunk = [lines[j] for j in range(i, i + min_lines) if lines[j] and not lines[j].startswith("#")]
                if len(chunk) >= min_lines:
                    key = "\n".join(chunk)
                    blocks.setdefault(key, []).append(rel_path)
        return sum(1 for paths in blocks.values() if len(paths) > 1)

    def _count_empty_files(self, parsed: Dict[str, tuple]) -> int:
        count = 0
        for rel_path, (_, content) in parsed.items():
            if not content.strip():
                count += 1
        return count

    def _count_dead_files(self, parsed: Dict[str, tuple]) -> int:
        imported_modules = set()
        entry_points = {"main.py", "app.py", "cli.py", "__init__.py", "setup.py", "manage.py"}
        for rel_path, (tree, _) in parsed.items():
            base = os.path.basename(rel_path)
            if base in entry_points or "test" in rel_path.lower() or base.startswith("__"):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_modules.add(node.names[0].name.split(".")[0])
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_modules.add(node.module.split(".")[0])

        dead = 0
        for rel_path in parsed.keys():
            mod_name = os.path.splitext(rel_path)[0].replace(os.sep, ".")
            base = os.path.basename(rel_path)
            if base in entry_points or "test" in rel_path.lower() or base.startswith("__"):
                continue
            if mod_name not in imported_modules:
                dead += 1
        return dead

    def _count_dead_code(self, parsed: Dict[str, tuple]) -> int:
        defined: Dict[str, str] = {}
        called = set()
        for rel_path, (tree, _) in parsed.items():
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not node.name.startswith("__"):
                        defined[node.name] = rel_path
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        called.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        called.add(node.func.attr)
        return sum(1 for name in defined if name.startswith("_") and name not in called)
