from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from .project_metadata import ProjectMetadata


@dataclass
class WorkspaceProject:
    metadata: ProjectMetadata
    planner_state: Dict[str, Any] = field(default_factory=dict)
    executor_state: Dict[str, Any] = field(default_factory=dict)
    repair_state: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    reports: List[Any] = field(default_factory=list)

    @property
    def project_id(self):
        return self.metadata.project_id

    @property
    def name(self):
        return self.metadata.name

    @property
    def status(self):
        return self.metadata.status

    def touch(self, status=None):
        if status:
            self.metadata.status = str(status)
        self.metadata.updated_at = datetime.now(timezone.utc).isoformat()
        return self

    def to_dict(self):
        return {
            "metadata": self.metadata.to_dict(),
            "planner_state": self.planner_state,
            "executor_state": self.executor_state,
            "repair_state": self.repair_state,
            "memory": self.memory,
            "timeline": self.timeline,
            "metrics": self.metrics,
            "reports": self.reports,
        }

    @classmethod
    def from_dict(cls, value):
        return cls(ProjectMetadata.from_dict(value["metadata"]), dict(value.get("planner_state", {})),
                   dict(value.get("executor_state", {})), dict(value.get("repair_state", {})),
                   dict(value.get("memory", {})), list(value.get("timeline", [])),
                   dict(value.get("metrics", {})), list(value.get("reports", [])))
