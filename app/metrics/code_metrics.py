"""Code quality and complexity metrics for generated code.

Analyzes generated code for:
  - lines of code
  - cyclomatic complexity
  - function/class count
  - import dependencies
  - documentation ratio
  - duplication estimate

Example output:
  Files Generated    182
  Total Lines        12,450
  Avg Complexity     4.2
  Functions          342
  Classes            28
  Documentation      78%
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class CodeFileMetrics:
    """Metrics for a single code file."""

    filepath: str = ""
    lines: int = 0
    code_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    functions: int = 0
    classes: int = 0
    imports: int = 0
    cyclomatic_complexity: int = 0
    avg_function_length: float = 0.0
    documentation_ratio: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filepath": self.filepath,
            "lines": self.lines,
            "code_lines": self.code_lines,
            "blank_lines": self.blank_lines,
            "comment_lines": self.comment_lines,
            "functions": self.functions,
            "classes": self.classes,
            "imports": self.imports,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "avg_function_length": round(self.avg_function_length, 2),
            "documentation_ratio": round(self.documentation_ratio, 3),
        }


@dataclass
class CodeMetricsReport:
    """Aggregated code metrics for a project."""

    files_count: int = 0
    total_lines: int = 0
    total_code_lines: int = 0
    total_blank_lines: int = 0
    total_comment_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_imports: int = 0
    total_complexity: int = 0
    avg_complexity: float = 0.0
    avg_function_length: float = 0.0
    documentation_ratio: float = 0.0
    duplication_estimate: float = 0.0
    files: List[CodeFileMetrics] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files_count": self.files_count,
            "total_lines": self.total_lines,
            "total_code_lines": self.total_code_lines,
            "total_blank_lines": self.total_blank_lines,
            "total_comment_lines": self.total_comment_lines,
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "total_imports": self.total_imports,
            "total_complexity": self.total_complexity,
            "avg_complexity": round(self.avg_complexity, 2),
            "avg_function_length": round(self.avg_function_length, 2),
            "documentation_ratio": round(self.documentation_ratio, 3),
            "duplication_estimate": round(self.duplication_estimate, 3),
            "files": [f.to_dict() for f in self.files],
        }


class CodeMetricsAnalyzer:
    """Analyze code quality and complexity metrics."""

    def __init__(self, metrics_path: str = os.path.join("data", "code_metrics.json")):
        self.metrics_path = metrics_path
        self._reports: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.isfile(self.metrics_path):
            try:
                with open(self.metrics_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self._reports = raw
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.metrics_path), exist_ok=True)
        with open(self.metrics_path, "w", encoding="utf-8") as f:
            json.dump(self._reports, f, indent=2, default=str)

    def analyze_file(self, filepath: str, content: str) -> CodeFileMetrics:
        """Analyze a single code file."""
        lines = content.split("\n")
        total_lines = len(lines)
        blank_lines = sum(1 for line in lines if not line.strip())
        comment_lines = self._count_comment_lines(lines, filepath)
        code_lines = total_lines - blank_lines - comment_lines

        functions = self._count_functions(content, filepath)
        classes = self._count_classes(content, filepath)
        imports = self._count_imports(content, filepath)
        complexity = self._estimate_complexity(content)

        avg_func_length = code_lines / max(1, functions)
        doc_ratio = comment_lines / max(1, total_lines)

        return CodeFileMetrics(
            filepath=filepath,
            lines=total_lines,
            code_lines=code_lines,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
            functions=functions,
            classes=classes,
            imports=imports,
            cyclomatic_complexity=complexity,
            avg_function_length=avg_func_length,
            documentation_ratio=doc_ratio,
        )

    def analyze_project(self, files: Dict[str, str]) -> CodeMetricsReport:
        """Analyze an entire project's code files."""
        file_metrics = []
        for filepath, content in files.items():
            file_metrics.append(self.analyze_file(filepath, content))

        report = CodeMetricsReport(
            files_count=len(file_metrics),
            total_lines=sum(f.lines for f in file_metrics),
            total_code_lines=sum(f.code_lines for f in file_metrics),
            total_blank_lines=sum(f.blank_lines for f in file_metrics),
            total_comment_lines=sum(f.comment_lines for f in file_metrics),
            total_functions=sum(f.functions for f in file_metrics),
            total_classes=sum(f.classes for f in file_metrics),
            total_imports=sum(f.imports for f in file_metrics),
            total_complexity=sum(f.cyclomatic_complexity for f in file_metrics),
            files=file_metrics,
        )

        report.avg_complexity = report.total_complexity / max(1, report.files_count)
        report.avg_function_length = report.total_code_lines / max(1, report.total_functions)
        report.documentation_ratio = report.total_comment_lines / max(1, report.total_lines)
        report.duplication_estimate = self._estimate_duplication(file_metrics)

        self._reports.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report": report.to_dict(),
        })
        self._save()

        return report

    def _count_comment_lines(self, lines: List[str], filepath: str) -> int:
        """Count comment lines based on file extension."""
        ext = os.path.splitext(filepath)[1].lower()
        comment_patterns = {
            ".py": (r"^\s*#", r'^\s*"""', r"^\s*'''"),
            ".js": (r"^\s*//", r"^\s*/\*"),
            ".ts": (r"^\s*//", r"^\s*/\*"),
            ".java": (r"^\s*//", r"^\s*/\*"),
            ".cpp": (r"^\s*//", r"^\s*/\*"),
            ".c": (r"^\s*//", r"^\s*/\*"),
            ".go": (r"^\s*//",),
            ".rs": (r"^\s*//",),
        }
        patterns = comment_patterns.get(ext, (r"^\s*#",))
        count = 0
        in_block_comment = False
        for line in lines:
            stripped = line.strip()
            if in_block_comment:
                count += 1
                if "*/" in stripped:
                    in_block_comment = False
                continue
            for pat in patterns:
                if re.match(pat, stripped):
                    count += 1
                    if "/*" in pat:
                        in_block_comment = "*/" not in stripped
                    break
        return count

    def _count_functions(self, content: str, filepath: str) -> int:
        """Count function definitions."""
        ext = os.path.splitext(filepath)[1].lower()
        patterns = {
            ".py": r"^\s*def\s+\w+",
            ".js": r"^\s*(function\s+\w+|const\s+\w+\s*=\s*(async\s*)?\(|"
                   r"\w+\s*:\s*(async\s*)?\()",
            ".ts": r"^\s*(function\s+\w+|const\s+\w+\s*=\s*(async\s*)?\(|"
                   r"\w+\s*:\s*(async\s*)?\()",
            ".java": r"^\s*(public|private|protected)?\s*\w+\s+\w+\s*\(",
            ".cpp": r"^\s*\w+\s+\w+\s*\([^)]*\)\s*\{",
            ".c": r"^\s*\w+\s+\w+\s*\([^)]*\)\s*\{",
            ".go": r"^func\s+\w+",
            ".rs": r"^fn\s+\w+",
        }
        pattern = patterns.get(ext, r"^\s*def\s+\w+")
        return len(re.findall(pattern, content, re.MULTILINE))

    def _count_classes(self, content: str, filepath: str) -> int:
        """Count class definitions."""
        ext = os.path.splitext(filepath)[1].lower()
        patterns = {
            ".py": r"^\s*class\s+\w+",
            ".js": r"^\s*class\s+\w+",
            ".ts": r"^\s*class\s+\w+",
            ".java": r"^\s*(public|private|protected)?\s*class\s+\w+",
            ".cpp": r"^\s*class\s+\w+",
            ".c": r"^\s*struct\s+\w+",
            ".go": r"^type\s+\w+\s+struct",
            ".rs": r"^\s*(pub\s+)?struct\s+\w+|^\s*(pub\s+)?enum\s+\w+",
        }
        pattern = patterns.get(ext, r"^\s*class\s+\w+")
        return len(re.findall(pattern, content, re.MULTILINE))

    def _count_imports(self, content: str, filepath: str) -> int:
        """Count import statements."""
        ext = os.path.splitext(filepath)[1].lower()
        patterns = {
            ".py": r"^\s*(import\s+|from\s+\w+\s+import)",
            ".js": r"^\s*(import\s+|require\()",
            ".ts": r"^\s*(import\s+|require\()",
            ".java": r"^\s*import\s+",
            ".cpp": r"^\s*#include\s+",
            ".c": r"^\s*#include\s+",
            ".go": r"^\s*import\s+",
            ".rs": r"^\s*use\s+",
        }
        pattern = patterns.get(ext, r"^\s*import\s+")
        return len(re.findall(pattern, content, re.MULTILINE))

    def _estimate_complexity(self, content: str) -> int:
        """Estimate cyclomatic complexity based on control flow keywords."""
        control_flow = [
            r"\bif\b", r"\belse\b", r"\belif\b", r"\bfor\b", r"\bwhile\b",
            r"\bcase\b", r"\bswitch\b", r"\bcatch\b", r"\bexcept\b",
            r"\band\b", r"\bor\b", r"\?\:", r"\?\.",
        ]
        complexity = 1
        for pattern in control_flow:
            complexity += len(re.findall(pattern, content))
        return complexity

    def _estimate_duplication(self, file_metrics: List[CodeFileMetrics]) -> float:
        """Estimate code duplication based on similar file sizes and structures."""
        if len(file_metrics) < 2:
            return 0.0
        sizes = [f.lines for f in file_metrics if f.lines > 0]
        if not sizes:
            return 0.0
        avg_size = sum(sizes) / len(sizes)
        similar = sum(1 for s in sizes if abs(s - avg_size) < avg_size * 0.3)
        return min(1.0, similar / max(1, len(sizes)))

    def format_report(self, report: CodeMetricsReport) -> str:
        """Format a human-readable code metrics report."""
        lines = [
            "Code Metrics Report",
            "=" * 50,
            f"  Files Generated:    {report.files_count}",
            f"  Total Lines:        {report.total_lines:,}",
            f"  Code Lines:         {report.total_code_lines:,}",
            f"  Comment Lines:      {report.total_comment_lines:,}",
            f"  Blank Lines:        {report.total_blank_lines:,}",
            f"  Functions:          {report.total_functions}",
            f"  Classes:            {report.total_classes}",
            f"  Imports:            {report.total_imports}",
            f"  Avg Complexity:     {report.avg_complexity:.1f}",
            f"  Avg Function Len:   {report.avg_function_length:.1f} lines",
            f"  Documentation:      {report.documentation_ratio:.0%}",
            f"  Duplication Est:    {report.duplication_estimate:.0%}",
        ]
        return "\n".join(lines)
