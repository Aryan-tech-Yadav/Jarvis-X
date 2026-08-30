"""Project scanner orchestrator.

Coordinates all scanner modules to produce a complete project report:
  - FileScanner: discovers Python files
  - PythonParser: parses AST
  - DependencyScanner: builds import graph
  - MetricsCollector: computes per-file metrics
  - ReportWriter: generates reports
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.self_improvement.scanner.dependency_scanner import DependencyScanner, DependencyGraph
from app.self_improvement.scanner.file_scanner import FileScanner, FileScannerResult
from app.self_improvement.scanner.metrics_collector import MetricsCollector, FileMetrics
from app.self_improvement.scanner.python_parser import PythonParser
from app.self_improvement.scanner.report_writer import ProjectReport, ReportWriter


@dataclass
class ScanResult:
    """Final scan result combining all scanner outputs."""

    project_path: str
    scan_duration: float = 0.0
    file_scan: Optional[FileScannerResult] = None
    parsed_files: Dict[str, Any] = field(default_factory=dict)
    dependency_graph: Optional[DependencyGraph] = None
    metrics: Dict[str, FileMetrics] = field(default_factory=dict)
    report: Optional[ProjectReport] = None
    report_paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "project_path": self.project_path,
            "scan_duration": round(self.scan_duration, 3),
            "file_scan": self.file_scan.to_dict() if self.file_scan else None,
            "parsed_files_count": len(self.parsed_files),
            "dependency_graph": self.dependency_graph.to_dict() if self.dependency_graph else None,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "report": self.report.to_dict() if self.report else None,
            "report_paths": dict(self.report_paths),
        }


class ProjectScanner:
    """Orchestrate project scanning pipeline.

    Usage:
        scanner = ProjectScanner(root="D:/Jarvis_Project/Jarvis-X")
        result = scanner.scan()
    """

    def __init__(self, root: str | os.PathLike[str], reports_dir: str = "reports"):
        self.root = os.path.abspath(root)
        self.reports_dir = reports_dir
        self.file_scanner = FileScanner(self.root)
        self.parser = PythonParser()
        self.dependency_scanner = DependencyScanner(self.root)
        self.metrics_collector = MetricsCollector()
        self.report_writer = ReportWriter(reports_dir)

    def scan(self) -> ScanResult:
        """Run full project scan.

        Returns:
            ScanResult with all scan data and generated reports.
        """
        started = time.perf_counter()
        Logger.info(f"[ProjectScanner] Scanning: {self.root}")

        # Phase 1: Discover files
        file_scan = self.file_scanner.scan()
        Logger.info(f"[ProjectScanner] Found {file_scan.total_files} Python files")

        # Phase 2: Parse files
        file_contents: Dict[str, str] = {}
        for rel_path in file_scan.python_files:
            abs_path = os.path.join(self.root, rel_path)
            try:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    file_contents[rel_path] = f.read()
            except (OSError, UnicodeDecodeError):
                continue

        parsed_files = self.parser.parse_files(file_contents)
        Logger.info(f"[ProjectScanner] Parsed {len(parsed_files)} files")

        # Phase 3: Build dependency graph
        dep_graph = self.dependency_scanner.scan(file_contents)
        Logger.info(f"[ProjectScanner] Found {len(dep_graph.edges)} dependencies, {len(dep_graph.cycles)} cycles")

        # Phase 4: Collect metrics
        metrics = self.metrics_collector.collect_batch(file_contents, parsed_files)
        Logger.info(f"[ProjectScanner] Collected metrics for {len(metrics)} files")

        # Phase 5: Generate report
        report = self._build_report(file_scan, parsed_files, dep_graph, metrics)
        report_paths = self.report_writer.write_all(report)
        Logger.info(f"[ProjectScanner] Reports written: {list(report_paths.values())}")

        duration = time.perf_counter() - started
        Logger.success(f"[ProjectScanner] Scan complete in {duration:.2f}s")

        return ScanResult(
            project_path=self.root,
            scan_duration=duration,
            file_scan=file_scan,
            parsed_files={k: v.to_dict() for k, v in parsed_files.items()},
            dependency_graph=dep_graph,
            metrics=dict(metrics),
            report=report,
            report_paths=report_paths,
        )

    def _build_report(self, file_scan: FileScannerResult,
                      parsed_files: Dict[str, Any],
                      dep_graph: DependencyGraph,
                      metrics: Dict[str, FileMetrics]) -> ProjectReport:
        """Build final project report."""
        # Summary
        total_classes = sum(len(v.classes) for v in parsed_files.values())
        total_functions = sum(len(v.functions) for v in parsed_files.values())
        total_imports = sum(len(v.imports) for v in parsed_files.values())
        total_loc = sum(m.loc for m in metrics.values())
        total_complexity = sum(m.complexity for m in metrics.values())
        avg_complexity = round(total_complexity / max(1, len(metrics)), 1)

        # Issues
        issues = []
        for path, metric in metrics.items():
            if metric.complexity > 20:
                issues.append(f"{path}: High complexity ({metric.complexity})")
            if metric.max_function_length > 60:
                issues.append(f"{path}: Long function ({metric.max_function_length} lines)")
            if metric.loc > 500:
                issues.append(f"{path}: Large file ({metric.loc} LOC)")

        for cycle in dep_graph.cycles:
            issues.append(f"Circular dependency: {' -> '.join(cycle)}")

        for edge in dep_graph.unused_imports:
            issues.append(f"Unused import: {edge.source} -> {edge.target}")

        # Top files by complexity
        top_complex = sorted(metrics.values(), key=lambda m: m.complexity, reverse=True)[:5]
        top_files = [
            {"path": m.path, "complexity": m.complexity, "loc": m.loc}
            for m in top_complex
        ]

        summary = {
            "files": file_scan.total_files,
            "classes": total_classes,
            "functions": total_functions,
            "imports": total_imports,
            "loc": total_loc,
            "complexity_score": avg_complexity,
            "dead_files": file_scan.python_files.count([p for p in file_scan.python_files if metrics.get(p, FileMetrics(path=p)).loc == 0]),
            "circular_dependencies": len(dep_graph.cycles),
            "duplicate_code": 0,  # Placeholder - could be enhanced
        }

        report = ProjectReport(
            project_path=self.root,
            summary=summary,
            files=top_files,
            dependencies=dep_graph.to_dict(),
            issues=issues[:50],
            metadata={
                "scanned_dirs": file_scan.scanned_dirs,
                "parsed_files": len(parsed_files),
            },
        )
        return report
