"""Self-improvement system analyzer.

Scans the Jarvis-X codebase and produces a structured analysis report
containing weaknesses, smells, and improvement opportunities.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.quality.qa_engine import QAEngine
from app.quality.models.quality_result import QualityScore, StaticAnalysisResult


@dataclass
class SystemAnalysis:
    """Complete system analysis report."""

    project_path: str
    analyzed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    quality_score: Optional[QualityScore] = None
    static_analysis: Optional[StaticAnalysisResult] = None
    module_count: int = 0
    total_lines: int = 0
    python_files: List[str] = field(default_factory=list)
    large_files: List[Dict[str, Any]] = field(default_factory=list)
    improvement_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_path": self.project_path,
            "analyzed_at": self.analyzed_at,
            "quality_score": self.quality_score.to_dict() if self.quality_score else None,
            "static_analysis": self.static_analysis.to_dict() if self.static_analysis else None,
            "module_count": self.module_count,
            "total_lines": self.total_lines,
            "python_files": list(self.python_files),
            "large_files": list(self.large_files),
            "improvement_opportunities": list(self.improvement_opportunities),
            "metrics": dict(self.metrics),
        }


class SystemAnalyzer:
    """Analyze the Jarvis-X codebase for self-improvement opportunities."""

    def __init__(self, project_path: str = "."):
        self.project_path = os.path.abspath(project_path)
        self.qa_engine = QAEngine(self.project_path)

    def analyze(self) -> SystemAnalysis:
        """Run full system analysis."""
        Logger.info(f"[SystemAnalyzer] Analyzing project at: {self.project_path}")
        
        analysis = SystemAnalysis(project_path=self.project_path)
        
        # Run QA engine
        try:
            quality_score, static_result = self.qa_engine.evaluate_quality(self.project_path)
            analysis.quality_score = quality_score
            analysis.static_analysis = static_result
        except Exception as exc:
            Logger.error(f"[SystemAnalyzer] QA engine failed: {exc}")
        
        # Collect file metrics
        self._collect_file_metrics(analysis)
        
        # Generate improvement opportunities from issues
        self._generate_opportunities(analysis)
        
        Logger.success(f"[SystemAnalyzer] Analysis complete: {len(analysis.improvement_opportunities)} opportunities found")
        return analysis

    def _collect_file_metrics(self, analysis: SystemAnalysis):
        """Collect basic file metrics."""
        python_files = []
        total_lines = 0
        large_files = []
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", "dist", "build", "workspace"}]
            
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, self.project_path)
                python_files.append(rel_path)
                
                try:
                    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    lines = len(content.splitlines())
                    total_lines += lines
                    
                    if lines > 500:
                        large_files.append({
                            "path": rel_path,
                            "lines": lines,
                            "reason": f"File exceeds 500 lines ({lines} lines)",
                            "priority": "high" if lines > 1000 else "medium",
                        })
                except (OSError, UnicodeDecodeError):
                    continue
        
        analysis.python_files = sorted(python_files)
        analysis.total_lines = total_lines
        analysis.large_files = sorted(large_files, key=lambda x: x["lines"], reverse=True)
        analysis.module_count = len(python_files)
        
        analysis.metrics = {
            "module_count": analysis.module_count,
            "total_lines": total_lines,
            "large_files_count": len(large_files),
            "avg_lines_per_file": round(total_lines / max(1, len(python_files)), 1),
        }

    def _generate_opportunities(self, analysis: SystemAnalysis):
        """Convert analysis issues into improvement opportunities."""
        opportunities = []
        
        # From static analysis issues
        if analysis.static_analysis:
            for issue in analysis.static_analysis.issues:
                opp = {
                    "id": f"issue-{len(opportunities)+1}",
                    "type": "bug" if issue.severity.value in ("critical", "high") else "refactor",
                    "category": issue.category.value,
                    "severity": issue.severity.value,
                    "file": issue.file,
                    "line": issue.line,
                    "rule": issue.rule,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "priority": self._severity_to_priority(issue.severity.value),
                    "estimated_effort": self._estimate_effort(issue.severity.value),
                }
                opportunities.append(opp)
        
        # From large files
        for lf in analysis.large_files:
            opp = {
                "id": f"large-file-{len(opportunities)+1}",
                "type": "refactor",
                "category": "architecture",
                "severity": "medium",
                "file": lf["path"],
                "line": 1,
                "rule": "large_file",
                "message": lf["reason"],
                "suggestion": "Split into smaller focused modules",
                "priority": lf["priority"],
                "estimated_effort": "high" if lf["lines"] > 1000 else "medium",
            }
            opportunities.append(opp)
        
        # From quality score suggestions
        if analysis.quality_score:
            for suggestion in analysis.quality_score.suggestions:
                if suggestion and "senior engineering" not in suggestion.lower():
                    opp = {
                        "id": f"suggestion-{len(opportunities)+1}",
                        "type": "improvement",
                        "category": "quality",
                        "severity": "low",
                        "file": "project",
                        "line": 1,
                        "rule": "quality_improvement",
                        "message": suggestion,
                        "suggestion": suggestion,
                        "priority": "low",
                        "estimated_effort": "medium",
                    }
                    opportunities.append(opp)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        opportunities.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
        
        analysis.improvement_opportunities = opportunities

    @staticmethod
    def _severity_to_priority(severity: str) -> str:
        mapping = {
            "critical": "high",
            "high": "high",
            "medium": "medium",
            "low": "low",
            "info": "low",
        }
        return mapping.get(severity, "medium")

    @staticmethod
    def _estimate_effort(severity: str) -> str:
        mapping = {
            "critical": "high",
            "high": "medium",
            "medium": "low",
            "low": "low",
            "info": "low",
        }
        return mapping.get(severity, "medium")
