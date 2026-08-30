"""Quality checker for self-improvement.

Scores individual files on maintainability, complexity, code smells,
duplicates, and risk.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FileQualityReport:
    """Quality report for a single file."""

    path: str
    maintainability: int = 0
    complexity: int = 0
    code_smells: int = 0
    duplicates: int = 0
    risk: str = "low"
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "maintainability": self.maintainability,
            "complexity": self.complexity,
            "code_smells": self.code_smells,
            "duplicates": self.duplicates,
            "risk": self.risk,
            "issues": list(self.issues),
            "suggestions": list(self.suggestions),
        }


class QualityChecker:
    """Evaluate file-level quality metrics."""

    MAX_FUNCTION_LINES = 60
    MAX_CLASS_LINES = 400
    HIGH_COMPLEXITY_THRESHOLD = 10

    def __init__(self, project_path: str = "."):
        self.project_path = os.path.abspath(project_path)
        self.ignored_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build"}

    def check_file(self, file_path: str) -> FileQualityReport:
        """Check quality of a single file."""
        report = FileQualityReport(path=file_path)

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
        except (OSError, SyntaxError, UnicodeDecodeError):
            report.risk = "high"
            report.issues.append("File cannot be parsed")
            return report

        lines = content.splitlines()
        report.maintainability = self._score_maintainability(content, tree)
        report.complexity = self._compute_complexity(tree)
        report.code_smells = self._count_smells(tree, content)
        report.duplicates = self._count_local_duplicates(content)
        report.risk = self._assess_risk(report)

        if report.complexity > self.HIGH_COMPLEXITY_THRESHOLD:
            report.issues.append(f"High complexity: {report.complexity}")
            report.suggestions.append("Simplify conditional logic")
        if report.code_smells > 5:
            report.issues.append(f"Many code smells: {report.code_smells}")
            report.suggestions.append("Refactor to reduce smells")
        if len(lines) > 500:
            report.issues.append(f"Large file: {len(lines)} lines")
            report.suggestions.append("Split into smaller modules")

        return report

    def check_project(self) -> List[FileQualityReport]:
        """Check quality of all Python files in the project."""
        reports = []
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, self.project_path)
                reports.append(self.check_file(rel_path))
        return sorted(reports, key=lambda r: r.maintainability)

    def _score_maintainability(self, content: str, tree: ast.AST) -> int:
        """Score maintainability 0-100."""
        lines = len(content.splitlines())
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))

        if lines == 0:
            return 100

        score = 100
        # Penalize large files
        if lines > 800:
            score -= 30
        elif lines > 500:
            score -= 20
        elif lines > 300:
            score -= 10

        # Penalize too many classes/functions
        if functions > 20:
            score -= 15
        if classes > 10:
            score -= 15

        # Penalize long functions
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, "end_lineno", node.lineno)
                if end_line - node.lineno + 1 > self.MAX_FUNCTION_LINES:
                    score -= 5

        return max(0, min(100, score))

    def _compute_complexity(self, tree: ast.AST) -> int:
        """Compute cyclomatic complexity."""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                complexity += len(node.generators)
            elif isinstance(node, ast.IfExp):
                complexity += 1
            elif isinstance(node, ast.Assert):
                complexity += 1
        return complexity

    def _count_smells(self, tree: ast.AST, content: str) -> int:
        """Count code smells."""
        smells = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_line = getattr(node, "end_lineno", node.lineno)
                if end_line - node.lineno + 1 > self.MAX_FUNCTION_LINES:
                    smells += 1
                if len(node.args.args) > 6:
                    smells += 1
            elif isinstance(node, ast.ClassDef):
                end_line = getattr(node, "end_lineno", node.lineno)
                methods = [m for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                if end_line - node.lineno + 1 > self.MAX_CLASS_LINES or len(methods) > 18:
                    smells += 1
            elif isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    smells += 1
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        smells += 1
        return smells

    def _count_local_duplicates(self, content: str) -> int:
        """Count duplicate blocks within a file."""
        lines = [line.strip() for line in content.splitlines()]
        blocks: Dict[str, int] = {}
        min_block = 4
        for i in range(len(lines) - min_block + 1):
            chunk = [lines[j] for j in range(i, i + min_block) if lines[j] and not lines[j].startswith("#")]
            if len(chunk) >= min_block:
                key = "\n".join(chunk)
                blocks[key] = blocks.get(key, 0) + 1
        return sum(1 for count in blocks.values() if count > 1)

    def _assess_risk(self, report: FileQualityReport) -> str:
        """Assess overall risk level."""
        score = 0
        if report.maintainability < 50:
            score += 3
        elif report.maintainability < 70:
            score += 1
        if report.complexity > self.HIGH_COMPLEXITY_THRESHOLD:
            score += 2
        if report.code_smells > 10:
            score += 2
        elif report.code_smells > 5:
            score += 1
        if report.duplicates > 3:
            score += 1
        if score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        return "low"
