"""Risk engine for self-improvement.

Estimates risk of proposed improvements to prevent breaking changes.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RiskAssessment:
    """Risk assessment for a single improvement."""

    task_id: str
    risk_level: str = "medium"  # low, medium, high
    risk_score: float = 0.0  # 0.0 to 1.0
    factors: List[str] = field(default_factory=list)
    requires_approval: bool = False
    suggested_tests: List[str] = field(default_factory=list)
    rollback_strategy: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "risk_level": self.risk_level,
            "risk_score": round(self.risk_score, 2),
            "factors": list(self.factors),
            "requires_approval": self.requires_approval,
            "suggested_tests": list(self.suggested_tests),
            "rollback_strategy": self.rollback_strategy,
        }


class RiskEngine:
    """Assess risk of proposed code improvements."""

    HIGH_RISK_THRESHOLD = 0.7
    MEDIUM_RISK_THRESHOLD = 0.4

    def assess(self, task: Dict[str, Any], file_content: str = "") -> RiskAssessment:
        """Assess risk of a single improvement task."""
        task_id = task.get("id", "unknown")
        risk_factors = []
        score = 0.0
        
        # Factor 1: Task type
        task_type = task.get("type", "refactor")
        type_scores = {
            "bug": 0.2,
            "refactor": 0.5,
            "performance": 0.3,
            "security": 0.3,
            "documentation": 0.1,
            "testing": 0.1,
        }
        score += type_scores.get(task_type, 0.5)
        
        # Factor 2: Explicit risk level (weighted higher)
        explicit_risk = task.get("risk", "medium")
        risk_scores = {"low": 0.1, "medium": 0.5, "high": 0.9}
        score += risk_scores.get(explicit_risk, 0.5) * 1.5  # Weight explicit risk 1.5x
        
        # Factor 3: File complexity (if content provided)
        if file_content:
            complexity = self._estimate_complexity(file_content)
            if complexity > 10:
                risk_factors.append("High cyclomatic complexity")
                score += 0.2
            if len(file_content.splitlines()) > 500:
                risk_factors.append("Large file (>500 lines)")
                score += 0.15
        
        # Factor 4: Core module detection
        file_path = task.get("file", "")
        if any(core in file_path.lower() for core in ["kernel", "brain", "core", "engine", "manager"]):
            risk_factors.append("Core module modification")
            score += 0.2
        
        # Factor 5: Effort estimation
        effort = task.get("effort", "medium")
        effort_scores = {"low": 0.1, "medium": 0.3, "high": 0.5}
        score += effort_scores.get(effort, 0.3)
        
        # Normalize score
        score = min(1.0, max(0.0, score / 3.0))
        
        # Determine risk level
        if score >= self.HIGH_RISK_THRESHOLD:
            risk_level = "high"
            requires_approval = True
        elif score >= self.MEDIUM_RISK_THRESHOLD:
            risk_level = "medium"
            requires_approval = False
        else:
            risk_level = "low"
            requires_approval = False
        
        # Generate suggested tests
        suggested_tests = self._suggest_tests(task, file_content)
        rollback_strategy = self._suggest_rollback(task)
        
        return RiskAssessment(
            task_id=task_id,
            risk_level=risk_level,
            risk_score=score,
            factors=risk_factors,
            requires_approval=requires_approval,
            suggested_tests=suggested_tests,
            rollback_strategy=rollback_strategy,
        )

    def assess_batch(self, tasks: List[Dict[str, Any]]) -> List[RiskAssessment]:
        """Assess risk for multiple tasks."""
        return [self.assess(task) for task in tasks]

    @staticmethod
    def _estimate_complexity(content: str) -> int:
        """Estimate cyclomatic complexity from source code."""
        try:
            tree = ast.parse(content)
            complexity = 1
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                    ast.ExceptHandler, ast.With, ast.AsyncWith)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            return complexity
        except SyntaxError:
            return 15  # High risk for unparseable code

    @staticmethod
    def _suggest_tests(task: Dict[str, Any], content: str) -> List[str]:
        """Suggest tests for the improvement."""
        tests = ["Run existing test suite"]
        
        task_type = task.get("type", "refactor")
        if task_type == "refactor":
            tests.append("Run regression tests")
            tests.append("Verify API compatibility")
        elif task_type == "bug":
            tests.append("Run specific bug reproduction test")
            tests.append("Verify fix doesn't break related functionality")
        elif task_type == "performance":
            tests.append("Run performance benchmarks")
            tests.append("Profile memory usage")
        elif task_type == "security":
            tests.append("Run security scan")
            tests.append("Verify no new vulnerabilities introduced")
        
        return tests

    @staticmethod
    def _suggest_rollback(task: Dict[str, Any]) -> str:
        """Suggest rollback strategy."""
        task_type = task.get("type", "refactor")
        if task_type == "refactor":
            return "Restore from version control or sandbox snapshot"
        elif task_type == "bug":
            return "Revert commit and restore previous version"
        elif task_type == "performance":
            return "Revert to previous optimized version"
        return "Restore from sandbox snapshot"
