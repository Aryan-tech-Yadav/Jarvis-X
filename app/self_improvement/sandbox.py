"""Sandbox builder for safe self-improvement.

Creates isolated sandboxes where improvements can be tested without
affecting the original codebase.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class Sandbox:
    """Isolated sandbox for testing improvements."""

    sandbox_id: str
    original_path: str
    sandbox_path: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "active"  # active, applied, discarded
    improvement_task_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sandbox_id": self.sandbox_id,
            "original_path": self.original_path,
            "sandbox_path": self.sandbox_path,
            "created_at": self.created_at,
            "status": self.status,
            "improvement_task_id": self.improvement_task_id,
            "metadata": dict(self.metadata),
        }


class SandboxBuilder:
    """Create and manage isolated sandboxes for code improvements."""

    def __init__(self, sandboxes_root: str = ".sandboxes"):
        self.sandboxes_root = sandboxes_root
        self._sandboxes: Dict[str, Sandbox] = {}

    def create(self, original_path: str, improvement_task_id: str = "") -> Sandbox:
        """Create a new sandbox by cloning the original project."""
        os.makedirs(self.sandboxes_root, exist_ok=True)
        
        sandbox_id = f"sandbox-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
        sandbox_path = os.path.join(self.sandboxes_root, sandbox_id)
        
        # Clone the original project
        if os.path.isdir(original_path):
            shutil.copytree(original_path, sandbox_path, ignore=shutil.ignore_patterns(
                ".git", "__pycache__", "*.pyc", ".pytest_cache", "*.egg-info"
            ))
        else:
            os.makedirs(sandbox_path, exist_ok=True)
        
        sandbox = Sandbox(
            sandbox_id=sandbox_id,
            original_path=os.path.abspath(original_path),
            sandbox_path=os.path.abspath(sandbox_path),
            improvement_task_id=improvement_task_id,
        )
        
        self._sandboxes[sandbox_id] = sandbox
        Logger.info(f"[SandboxBuilder] Created sandbox: {sandbox_id}")
        return sandbox

    def get(self, sandbox_id: str) -> Optional[Sandbox]:
        """Get sandbox by ID."""
        return self._sandboxes.get(sandbox_id)

    def apply_improvement(self, sandbox_id: str, file_path: str, new_content: str) -> bool:
        """Apply an improvement to a sandbox file."""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox or sandbox.status != "active":
            return False
        
        # Convert relative path to sandbox absolute path
        if os.path.isabs(file_path):
            target_path = os.path.join(sandbox.sandbox_path, os.path.relpath(file_path, sandbox.original_path))
        else:
            target_path = os.path.join(sandbox.sandbox_path, file_path)
        
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            Logger.info(f"[SandboxBuilder] Applied improvement to {target_path}")
            return True
        except (OSError, TypeError) as exc:
            Logger.error(f"[SandboxBuilder] Failed to apply improvement: {exc}")
            return False

    def discard(self, sandbox_id: str):
        """Discard a sandbox and clean up."""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox:
            return
        
        self._cleanup(sandbox.sandbox_path)
        sandbox.status = "discarded"
        Logger.info(f"[SandboxBuilder] Discarded sandbox: {sandbox_id}")

    def promote(self, sandbox_id: str, target_path: str) -> bool:
        """Promote sandbox changes to the target path."""
        sandbox = self._sandboxes.get(sandbox_id)
        if not sandbox or sandbox.status != "active":
            return False
        
        try:
            # Copy modified files from sandbox to target
            for root, dirs, files in os.walk(sandbox.sandbox_path):
                dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache"}]
                for filename in files:
                    sandbox_file = os.path.join(root, filename)
                    rel_path = os.path.relpath(sandbox_file, sandbox.sandbox_path)
                    target_file = os.path.join(target_path, rel_path)
                    
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    shutil.copy2(sandbox_file, target_file)
            
            sandbox.status = "applied"
            Logger.info(f"[SandboxBuilder] Promoted sandbox {sandbox_id} to {target_path}")
            return True
        except (OSError, shutil.Error) as exc:
            Logger.error(f"[SandboxBuilder] Failed to promote sandbox: {exc}")
            return False

    def cleanup_all(self):
        """Clean up all sandboxes."""
        for sandbox in self._sandboxes.values():
            if sandbox.status == "active":
                self._cleanup(sandbox.sandbox_path)
                sandbox.status = "discarded"
        self._sandboxes.clear()

    @staticmethod
    def _cleanup(path: str):
        """Remove a directory tree safely."""
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
        except (OSError, shutil.Error):
            pass

    def list_sandboxes(self) -> List[Dict[str, Any]]:
        """List all sandboxes."""
        return [sandbox.to_dict() for sandbox in self._sandboxes.values()]
