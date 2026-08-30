"""Shared Runtime Context.

Single source of truth for all runtime state.
All modules read/write through this context.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ProjectContext:
    """Project-specific context."""
    project_id: str = ""
    project_name: str = ""
    project_type: str = ""
    tech_stack: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)
    architecture: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    """Task-specific context."""
    task_id: str = ""
    task_name: str = ""
    intent: str = ""
    status: str = "pending"
    plan: List[Dict[str, Any]] = field(default_factory=list)
    current_step: int = 0
    dependencies: List[str] = field(default_factory=list)
    result: Any = None
    error: Optional[str] = None


@dataclass
class MemoryContext:
    """Memory context for runtime."""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    short_term: Dict[str, Any] = field(default_factory=dict)
    long_term: List[Dict[str, Any]] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricsContext:
    """Runtime metrics."""
    start_time: float = 0.0
    end_time: float = 0.0
    duration_seconds: float = 0.0
    files_generated: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    errors_fixed: int = 0
    quality_score: float = 0.0
    tokens_used: int = 0
    cost_estimate: float = 0.0


class RuntimeContext:
    """Shared context for Jarvis-X runtime.

    This is the single source of truth for all runtime state.
    Modules should NOT maintain separate state - they should use this context.

    Structure:
      - session_id: Unique runtime session
      - project: Project context (name, type, tech stack, artifacts)
      - current_task: Current task being executed
      - plan: Execution plan
      - memories: Conversation and long-term memory
      - knowledge: Retrieved knowledge and best practices
      - metrics: Runtime metrics
      - history: Execution history
    """

    def __init__(self):
        self.session_id = self._generate_session_id()
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at

        # Core contexts
        self.project = ProjectContext()
        self.current_task = TaskContext()
        self.memories = MemoryContext()
        self.metrics = MetricsContext()

        # Runtime state
        self.plan: List[Dict[str, Any]] = []
        self.knowledge: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.artifacts: List[str] = []
        self.config: Dict[str, Any] = {}
        self.state: str = "idle"

        # Event bus reference
        self.event_bus = None

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        return f"session_{uuid.uuid4().hex[:12]}"

    def update(self, **kwargs):
        """Update context fields.

        Args:
            **kwargs: Fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()

    def add_artifact(self, artifact_path: str):
        """Add artifact to project.

        Args:
            artifact_path: Path to artifact file/directory
        """
        if artifact_path not in self.artifacts:
            self.artifacts.append(artifact_path)
        if artifact_path not in self.project.artifacts:
            self.project.artifacts.append(artifact_path)

    def add_history(self, entry: Dict[str, Any]):
        """Add entry to execution history.

        Args:
            entry: History entry dict
        """
        entry["timestamp"] = datetime.now().isoformat()
        entry["session_id"] = self.session_id
        self.history.append(entry)

    def add_memory(self, role: str, content: str):
        """Add conversation memory.

        Args:
            role: Message role (user/assistant/system)
            content: Message content
        """
        self.memories.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })

    def get_short_term(self, key: str, default: Any = None) -> Any:
        """Get short-term memory value.

        Args:
            key: Memory key
            default: Default value if not found

        Returns:
            Memory value or default
        """
        return self.memories.short_term.get(key, default)

    def set_short_term(self, key: str, value: Any):
        """Set short-term memory value.

        Args:
            key: Memory key
            value: Memory value
        """
        self.memories.short_term[key] = value

    def add_knowledge(self, knowledge: Dict[str, Any]):
        """Add knowledge entry.

        Args:
            knowledge: Knowledge entry dict
        """
        self.knowledge.append(knowledge)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "state": self.state,
            "project": {
                "project_id": self.project.project_id,
                "project_name": self.project.project_name,
                "project_type": self.project.project_type,
                "tech_stack": self.project.tech_stack,
                "artifacts": self.project.artifacts,
            },
            "current_task": {
                "task_id": self.current_task.task_id,
                "task_name": self.current_task.task_name,
                "intent": self.current_task.intent,
                "status": self.current_task.status,
                "current_step": self.current_task.current_step,
            },
            "plan": self.plan,
            "artifacts": self.artifacts,
            "metrics": {
                "duration_seconds": self.metrics.duration_seconds,
                "files_generated": self.metrics.files_generated,
                "tests_passed": self.metrics.tests_passed,
                "tests_failed": self.metrics.tests_failed,
                "errors_fixed": self.metrics.errors_fixed,
                "quality_score": self.metrics.quality_score,
                "tokens_used": self.metrics.tokens_used,
                "cost_estimate": self.metrics.cost_estimate,
            },
            "history_count": len(self.history),
            "knowledge_count": len(self.knowledge),
        }

    def clone(self) -> RuntimeContext:
        """Create a copy of this context.

        Returns:
            New RuntimeContext with same data
        """
        import copy
        new_ctx = RuntimeContext()
        new_ctx.project = copy.deepcopy(self.project)
        new_ctx.current_task = copy.deepcopy(self.current_task)
        new_ctx.memories = copy.deepcopy(self.memories)
        new_ctx.metrics = copy.deepcopy(self.metrics)
        new_ctx.plan = copy.deepcopy(self.plan)
        new_ctx.knowledge = copy.deepcopy(self.knowledge)
        new_ctx.history = copy.deepcopy(self.history)
        new_ctx.artifacts = copy.deepcopy(self.artifacts)
        new_ctx.config = copy.deepcopy(self.config)
        new_ctx.state = self.state
        return new_ctx
