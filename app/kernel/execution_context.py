from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .state_machine import ExecutionStateMachine


@dataclass
class ExecutionContext:
    """Serializable per-run state for kernel graph execution and recovery."""

    goal: str
    project_id: Optional[str] = None
    project_path: Optional[str] = None
    run_id: str = field(default_factory=lambda: str(uuid4()))
    values: Dict[str, Any] = field(default_factory=dict)
    memory: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[Any] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    completed_nodes: List[str] = field(default_factory=list)
    attempts: Dict[str, int] = field(default_factory=dict)
    delayed_until: Dict[str, float] = field(default_factory=dict)
    current_node: Optional[str] = None
    failed_node: Optional[str] = None
    state_machine: ExecutionStateMachine = field(default_factory=ExecutionStateMachine)

    def __post_init__(self):
        if not isinstance(self.goal, str) or not self.goal.strip():
            raise ValueError("Execution goal cannot be empty")
        self.goal = self.goal.strip()

    @property
    def state(self):
        return self.state_machine.state

    def record(self, event_type, payload=None):
        entry = {"type": str(event_type), "payload": deepcopy(payload), "created_at": self._now()}
        self.timeline.append(entry)
        return entry

    def mark_started(self, node_id):
        self.current_node = str(node_id)
        self.attempts[self.current_node] = self.attempts.get(self.current_node, 0) + 1
        return self.record("KERNEL_NODE_STARTED", {"node_id": self.current_node, "attempt": self.attempts[self.current_node]})

    def mark_completed(self, node_id, result=None):
        node_id = str(node_id)
        if node_id not in self.completed_nodes:
            self.completed_nodes.append(node_id)
        if self.failed_node == node_id:
            self.failed_node = None
        self.current_node = None
        self.metrics["completed_nodes"] = len(self.completed_nodes)
        return self.record("KERNEL_NODE_COMPLETED", {"node_id": node_id, "result": deepcopy(result)})

    def mark_failed(self, node_id, error):
        self.current_node = None
        self.failed_node = str(node_id)
        error = str(error)
        if error and error not in self.errors:
            self.errors.append(error)
        return self.record("KERNEL_NODE_FAILED", {"node_id": self.failed_node, "error": error})

    def delay(self, node_id, until):
        node_id = str(node_id)
        self.delayed_until[node_id] = float(until)
        return self.record("KERNEL_NODE_DELAYED", {"node_id": node_id, "not_before": float(until)})

    def to_dict(self):
        return {
            "goal": self.goal,
            "project_id": self.project_id,
            "project_path": self.project_path,
            "run_id": self.run_id,
            "values": deepcopy(self.values),
            "memory": deepcopy(self.memory),
            "metrics": deepcopy(self.metrics),
            "artifacts": deepcopy(self.artifacts),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "timeline": deepcopy(self.timeline),
            "completed_nodes": list(self.completed_nodes),
            "attempts": dict(self.attempts),
            "delayed_until": dict(self.delayed_until),
            "current_node": self.current_node,
            "failed_node": self.failed_node,
            "state_machine": self.state_machine.to_dict(),
        }

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict):
            raise TypeError("Execution context payload must be a dictionary")
        return cls(
            goal=value["goal"], project_id=value.get("project_id"), project_path=value.get("project_path"),
            run_id=value.get("run_id") or str(uuid4()), values=deepcopy(value.get("values", {})),
            memory=deepcopy(value.get("memory", {})), metrics=deepcopy(value.get("metrics", {})),
            artifacts=deepcopy(value.get("artifacts", [])), warnings=list(value.get("warnings", [])),
            errors=list(value.get("errors", [])), timeline=deepcopy(value.get("timeline", [])),
            completed_nodes=list(value.get("completed_nodes", [])), attempts=dict(value.get("attempts", {})),
            delayed_until={str(key): float(item) for key, item in dict(value.get("delayed_until", {})).items()},
            current_node=value.get("current_node"), failed_node=value.get("failed_node"),
            state_machine=ExecutionStateMachine.from_dict(value.get("state_machine", {})),
        )

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()
