"""Base tool contract for the Jarvis-X tool ecosystem.

All tools must inherit from BaseTool and implement:
  - metadata (ToolMetadata)
  - run(action, **kwargs) -> dict
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolMetadata:
    """Metadata for a tool."""

    name: str
    description: str = ""
    actions: List[str] = field(default_factory=list)
    priority: int = 0
    enabled: bool = True
    version: str = "1.0.0"
    author: str = "Jarvis"
    permissions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "actions": list(self.actions),
            "permissions": list(self.permissions),
            "tags": list(self.tags),
            "enabled": self.enabled,
            "created_at": self.created_at,
        }


@dataclass
class ToolResult:
    """Unified result schema for all tool executions."""

    success: bool
    output: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": dict(self.metadata),
            "artifacts": list(self.artifacts),
            "duration": self.duration,
        }

    @classmethod
    def ok(cls, output: Any = None, **kwargs) -> ToolResult:
        return cls(success=True, output=output, **kwargs)

    @classmethod
    def fail(cls, error: str, **kwargs) -> ToolResult:
        return cls(success=False, error=error, **kwargs)

    @classmethod
    def from_value(cls, value: Any) -> "ToolResult":
        """Normalize legacy dictionaries and scalar tool returns."""
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                success=bool(value.get("success", False)),
                output=value.get("output"),
                error=value.get("error"),
                metadata=dict(value.get("metadata", {})),
                artifacts=list(value.get("artifacts", [])),
                duration=float(value.get("duration", value.get("execution_time", 0.0)) or 0.0),
            )
        return cls.ok(output=value)


class BaseTool:
    """Abstract base class for all Jarvis-X tools.

    Subclasses must set:
      - metadata: ToolMetadata instance
    And implement:
      - run(action, **kwargs) -> dict | ToolResult
    """

    metadata: ToolMetadata = None  # type: ignore[assignment]

    def __init__(self):
        # Always create instance-level metadata to avoid mutating class attributes
        class_meta = getattr(self.__class__, "metadata", None)
        if isinstance(class_meta, ToolMetadata):
            self.metadata = ToolMetadata(
                name=class_meta.name,
                description=class_meta.description,
                actions=list(class_meta.actions),
                priority=class_meta.priority,
                enabled=class_meta.enabled,
                version=class_meta.version,
                author=class_meta.author,
                permissions=list(class_meta.permissions),
                tags=list(class_meta.tags),
                created_at=class_meta.created_at,
            )
        elif self.metadata is None:
            self.metadata = ToolMetadata(name=getattr(self, "name", self.__class__.__name__))

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def description(self) -> str:
        return self.metadata.description

    @property
    def version(self) -> str:
        return self.metadata.version

    @property
    def permissions(self) -> List[str]:
        return self.metadata.permissions

    def run(self, action: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError

    def execute(self, request: Any = None, context: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Normalize inputs and delegate to run()."""
        payload = dict(kwargs)
        if isinstance(context, dict):
            payload.update(context)
        if isinstance(request, dict):
            payload.update(request)
        elif request is not None:
            payload.setdefault("action", request)
        if payload.get("action") is None and "action" in kwargs:
            payload["action"] = kwargs["action"]
        if payload.get("action") is None and context is not None and isinstance(context, dict):
            payload["action"] = context.get("action")
        result = self.run(**payload)
        if isinstance(result, ToolResult):
            return result.to_dict()
        return result

    def can_handle(self, action: str) -> bool:
        return action in self.metadata.actions

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.metadata.name!r} version={self.metadata.version!r}>"
