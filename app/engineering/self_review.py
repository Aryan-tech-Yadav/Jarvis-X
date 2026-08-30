"""Engineering self-review agent.

After a project is completed, the self-review agent asks reflective
questions and produces a structured improvement report.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.ai.ai_manager import AIManager
from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.quality.qa_engine import QAEngine
from app.utils.json_utils import clean_json


SELF_REVIEW_PROMPT = """
You are a senior engineering lead performing a post-mortem review of an
autonomously generated software project.

Given the following project context and benchmark results, answer these
questions concisely:

1. What went well?
2. What failed or had issues?
3. Can the architecture be improved?
4. Is there any duplicated code?
5. Are there any security issues?
6. Are there any performance bottlenecks?
7. What is the test coverage looking like?
8. Overall confidence in this code?

Return ONLY valid JSON.

Schema:
{{
  "what_went_well": [],
  "what_failed": [],
  "architecture_improvements": [],
  "duplicated_code": [],
  "security_issues": [],
  "performance_bottlenecks": [],
  "test_coverage_notes": "",
  "confidence": 0.0,
  "overall_suggestions": []
}}

Project Name: {project_name}
Goal: {goal}
Architecture: {architecture}
Benchmark: {benchmark}
Static Issues: {static_issues}
"""


@dataclass
class SelfReviewReport:
    """Structured self-review report."""

    project_name: str
    what_went_well: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    architecture_improvements: List[str] = field(default_factory=list)
    duplicated_code: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    performance_bottlenecks: List[str] = field(default_factory=list)
    test_coverage_notes: str = ""
    confidence: float = 0.0
    overall_suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "what_went_well": list(self.what_went_well),
            "what_failed": list(self.what_failed),
            "architecture_improvements": list(self.architecture_improvements),
            "duplicated_code": list(self.duplicated_code),
            "security_issues": list(self.security_issues),
            "performance_bottlenecks": list(self.performance_bottlenecks),
            "test_coverage_notes": self.test_coverage_notes,
            "confidence": round(self.confidence, 2),
            "overall_suggestions": list(self.overall_suggestions),
        }


class SelfReviewAgent:
    """Perform a self-review of a completed engineering project."""

    def __init__(self, ai=None, qa_engine=None):
        self.ai = ai or AIManager()
        self.qa_engine = qa_engine or QAEngine()

    def review(self, project_path: str, context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        if not isinstance(project_path, str) or not project_path.strip():
            return ExecutionResult.failed("Project path cannot be empty")

        context = context or {}
        project_name = os.path.basename(project_path.strip().rstrip(os.sep))

        try:
            # Gather static analysis for the review
            static_issues_summary = self._summarize_static_issues(project_path)
            benchmark = context.get("benchmark", {})
            architecture = context.get("architecture", {})

            prompt = SELF_REVIEW_PROMPT.format(
                project_name=project_name,
                goal=context.get("goal", project_name),
                architecture=json.dumps(architecture, indent=2),
                benchmark=json.dumps(benchmark, indent=2),
                static_issues=json.dumps(static_issues_summary, indent=2),
            )

            response = self.ai.ask(prompt)
            data = json.loads(clean_json(response))
            report = SelfReviewReport(project_name=project_name, **data)

            # Ensure confidence is numeric
            try:
                report.confidence = float(report.confidence)
            except (TypeError, ValueError):
                report.confidence = 0.0

            return ExecutionResult.completed(
                data=report.to_dict(),
                message="Self-review complete",
                metrics={"confidence": report.confidence},
            )
        except Exception as exc:
            Logger.error(f"Self-review failed: {exc}")
            return ExecutionResult.failed(
                str(exc),
                data=SelfReviewReport(project_name=project_name).to_dict(),
                warnings=[f"Self-review generation failed: {exc}"],
            )

    def _summarize_static_issues(self, project_path: str) -> Dict[str, Any]:
        try:
            static_result = self.qa_engine.static_analyzer.scan_directory(project_path)
            return {
                "complexity_level": static_result.complexity_level,
                "issues_count": len(static_result.issues),
                "dead_functions": len(static_result.dead_functions),
                "dead_files": len(static_result.dead_files),
                "duplicate_blocks": len(static_result.duplicate_blocks),
                "circular_imports": len(static_result.circular_imports),
            }
        except Exception:
            return {"error": "Static analysis unavailable"}
