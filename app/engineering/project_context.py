"""Engineering project context.

Holds the evolving state of a project as it passes through the
engineering pipeline stages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProjectContext:
    """Mutable context object for a single engineering project run."""

    goal: str = ""
    project_name: str = ""
    project_path: str = ""
    requirements: Dict[str, Any] = field(default_factory=dict)
    architecture: Dict[str, Any] = field(default_factory=dict)
    execution_plan: Dict[str, Any] = field(default_factory=dict)
    task_graph: Dict[str, Any] = field(default_factory=dict)
    benchmark: Dict[str, Any] = field(default_factory=dict)
    self_review: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    current_stage: str = "start"
    status: str = "pending"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "project_name": self.project_name,
            "project_path": self.project_path,
            "requirements": dict(self.requirements),
            "architecture": dict(self.architecture),
            "execution_plan": dict(self.execution_plan),
            "task_graph": dict(self.task_graph),
            "benchmark": dict(self.benchmark),
            "self_review": dict(self.self_review),
            "memory": dict(self.memory),
            "artifacts": list(self.artifacts),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "current_stage": self.current_stage,
            "status": self.status,
        }

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def add_artifact(self, artifact: str):
        if artifact and artifact not in self.artifacts:
            self.artifacts.append(artifact)

    def add_error(self, error: str):
        if error and error not in self.errors:
            self.errors.append(error)

    def add_warning(self, warning: str):
        if warning and warning not in self.warnings:
            self.warnings.append(warning)

    def summary(self) -> str:
        return (
            f"Project: {self.project_name or self.goal}\n"
            f"Status: {self.status}\n"
            f"Stage: {self.current_stage}\n"
            f"Path: {self.project_path}\n"
            f"Artifacts: {len(self.artifacts)}\n"
            f"Errors: {len(self.errors)}\n"
            f"Warnings: {len(self.warnings)}"
        )
