"""Persistent, isolated workspaces for managing multiple Jarvis-X projects."""

from .project import WorkspaceProject
from .workspace_manager import WorkspaceManager

__all__ = ["WorkspaceManager", "WorkspaceProject"]
