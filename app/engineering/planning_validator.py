"""Planning validator - verifies plans before execution.

Checks:
  - All imports exist
  - All functions are implemented
  - Folder structure is complete
  - No circular dependencies
  - All referenced files exist
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ValidationIssue:
    """A planning validation issue."""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # IMPORT, FUNCTION, STRUCTURE, DEPENDENCY
    message: str
    file: str = ""
    line: int = 0
    suggestion: str = ""


@dataclass
class ValidationResult:
    """Result of plan validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    missing_imports: List[str] = field(default_factory=list)
    missing_functions: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)
    circular_deps: List[List[str]] = field(default_factory=list)
    score: float = 0.0


class PlanningValidator:
    """Validate engineering plans before execution.

    Ensures the AI-generated plan is consistent and executable.
    """

    def __init__(self, project_path: str = ""):
        self.project_path = Path(project_path).resolve() if project_path else None

    def validate_plan(self, plan: Dict[str, Any], project_path: str = "") -> ValidationResult:
        """Validate a complete project plan.

        Args:
            plan: Project plan dict with files, modules, functions, etc.
            project_path: Path to generated project (if exists)

        Returns:
            ValidationResult with issues and score
        """
        self.project_path = Path(project_path).resolve() if project_path else self.project_path
        issues: List[ValidationIssue] = []

        # Validate structure
        if self.project_path and self.project_path.exists():
            issues.extend(self._validate_structure())
            issues.extend(self._validate_imports())
            issues.extend(self._validate_functions())
            issues.extend(self._validate_dependencies())

        missing_imports = [i.message for i in issues if i.category == "IMPORT" and i.severity == "CRITICAL"]
        missing_functions = [i.message for i in issues if i.category == "FUNCTION" and i.severity == "CRITICAL"]
        missing_files = [i.message for i in issues if i.category == "STRUCTURE" and i.severity == "CRITICAL"]
        circular_deps = [i.message for i in issues if i.category == "DEPENDENCY"]

        # Calculate score
        critical = len([i for i in issues if i.severity == "CRITICAL"])
        high = len([i for i in issues if i.severity == "HIGH"])
        medium = len([i for i in issues if i.severity == "MEDIUM"])

        score = max(0.0, 100.0 - (critical * 25.0) - (high * 10.0) - (medium * 3.0))

        return ValidationResult(
            valid=critical == 0,
            issues=issues,
            missing_imports=missing_imports,
            missing_functions=missing_functions,
            missing_files=missing_files,
            circular_deps=circular_deps,
            score=round(score, 2),
        )

    def _validate_structure(self) -> List[ValidationIssue]:
        """Validate project folder structure."""
        issues = []
        if not self.project_path or not self.project_path.exists():
            return issues

        required = {"src", "tests", "requirements.txt", "README.md"}
        found = set()
        for item in self.project_path.iterdir():
            found.add(item.name)

        for req in required:
            if req not in found:
                issues.append(ValidationIssue(
                    severity="MEDIUM",
                    category="STRUCTURE",
                    message=f"Missing required item: {req}",
                    suggestion=f"Create {req}",
                ))

        # Check for empty files
        for py_file in self.project_path.rglob("*.py"):
            if py_file.stat().st_size == 0:
                issues.append(ValidationIssue(
                    severity="HIGH",
                    category="STRUCTURE",
                    message=f"Empty file: {py_file.name}",
                    file=str(py_file.relative_to(self.project_path)),
                    suggestion="Implement the file contents",
                ))

        return issues

    def _validate_imports(self) -> List[ValidationIssue]:
        """Validate that all imports can be resolved."""
        issues = []
        if not self.project_path or not self.project_path.exists():
            return issues

        py_files = list(self.project_path.rglob("*.py"))
        module_names: Set[str] = set()
        for f in py_files:
            module_names.add(f.stem)

        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content)
            except SyntaxError:
                issues.append(ValidationIssue(
                    severity="CRITICAL",
                    category="IMPORT",
                    message=f"Syntax error in {py_file.name}",
                    file=str(py_file.relative_to(self.project_path)),
                    suggestion="Fix syntax errors before execution",
                ))
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        base = node.module.split(".")[0]
                        if base not in module_names and base not in {"os", "sys", "json", "re", "time", "datetime", "typing", "pathlib", "collections", "itertools", "functools", "math", "random", "string", "uuid", "io", "tempfile", "shutil", "subprocess", "threading", "multiprocessing", "asyncio", "http", "urllib", "socket", "email", "csv", "sqlite3", "logging", "argparse", "configparser", "hashlib", "base64", "enum", "dataclasses", "abc", "contextlib", "copy", "pprint", "traceback", "inspect", "importlib"}:
                            issues.append(ValidationIssue(
                                severity="CRITICAL",
                                category="IMPORT",
                                message=f"Cannot resolve import: {node.module}",
                                file=str(py_file.relative_to(self.project_path)),
                                line=node.lineno,
                                suggestion=f"Create module '{base}.py' or fix import path",
                            ))

                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        base = alias.name.split(".")[0]
                        if base not in module_names and base not in {"os", "sys", "json", "re", "time", "datetime", "typing", "pathlib", "collections", "itertools", "functools", "math", "random", "string", "uuid", "io", "tempfile", "shutil", "subprocess", "threading", "multiprocessing", "asyncio", "http", "urllib", "socket", "email", "csv", "sqlite3", "logging", "argparse", "configparser", "hashlib", "base64", "enum", "dataclasses", "abc", "contextlib", "copy", "pprint", "traceback", "inspect", "importlib"}:
                            issues.append(ValidationIssue(
                                severity="HIGH",
                                category="IMPORT",
                                message=f"Cannot resolve import: {alias.name}",
                                file=str(py_file.relative_to(self.project_path)),
                                line=node.lineno,
                                suggestion=f"Install package or create module '{base}.py'",
                            ))

        return issues

    def _validate_functions(self) -> List[ValidationIssue]:
        """Validate that all called functions exist."""
        issues = []
        if not self.project_path or not self.project_path.exists():
            return issues

        py_files = list(self.project_path.rglob("*.py"))
        defined_functions: Dict[str, Set[str]] = {}

        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content)
                module_name = py_file.stem
                defined_functions[module_name] = set()

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        defined_functions[module_name].add(node.name)
            except Exception:
                continue

        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content)
            except Exception:
                continue

            module_name = py_file.stem
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = None
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr

                    if func_name and not func_name.startswith("__"):
                        if func_name not in defined_functions.get(module_name, set()):
                            found_elsewhere = any(
                                func_name in funcs
                                for mod, funcs in defined_functions.items()
                                if mod != module_name
                            )
                            if not found_elsewhere:
                                issues.append(ValidationIssue(
                                    severity="HIGH",
                                    category="FUNCTION",
                                    message=f"Undefined function: {func_name}()",
                                    file=str(py_file.relative_to(self.project_path)),
                                    line=node.lineno,
                                    suggestion=f"Implement {func_name}() or fix the call",
                                ))

        return issues

    def _validate_dependencies(self) -> List[ValidationIssue]:
        """Validate no circular dependencies."""
        issues = []
        if not self.project_path or not self.project_path.exists():
            return issues

        py_files = list(self.project_path.rglob("*.py"))
        imports: Dict[str, Set[str]] = {}

        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(content)
                module_name = py_file.stem
                imports[module_name] = set()

                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        base = node.module.split(".")[0]
                        if base in {f.stem for f in py_files}:
                            imports[module_name].add(base)
            except Exception:
                continue

        # Simple cycle detection
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in imports.get(node, set()):
                if neighbor not in visited:
                    cycle = dfs(neighbor, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            path.pop()
            rec_stack.discard(node)
            return None

        for node in imports:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    issues.append(ValidationIssue(
                        severity="HIGH",
                        category="DEPENDENCY",
                        message=f"Circular dependency: {' -> '.join(cycle)}",
                        suggestion="Refactor to remove circular dependency",
                    ))

        return issues
