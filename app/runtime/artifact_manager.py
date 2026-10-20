"""Artifact Manager for project artifacts.

Manages:
  - Project directory structure
  - Artifact generation and storage
  - File organization
  - Report generation
"""

from __future__ import annotations

import json
import os
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ManagedArtifact:
    """Metadata and content for a managed project artifact."""

    artifact_id: str
    name: str
    artifact_type: str
    content: str
    created_by: str = "unknown"
    tags: List[str] = field(default_factory=list)
    checksum: str = ""


class ArtifactManager:
    """Manages project artifacts and directory structure.

    Standard project structure:
      workspace/project/
        plan.md
        requirements.md
        architecture.md
        code/
        tests/
        benchmark.json
        report.md
        metrics.json
        logs/
        reflections/
    """

    def __init__(self, base_workspace: str = "workspace"):
        self.base_workspace = Path(base_workspace).resolve()
        self.base_workspace.mkdir(parents=True, exist_ok=True)
        self._artifacts: List[ManagedArtifact] = []

    def add(
        self,
        name: str,
        artifact_type: str,
        content: Any,
        created_by: str = "unknown",
        tags: Optional[List[str]] = None,
    ) -> ManagedArtifact:
        """Register an artifact and return its metadata.

        Preserves compatibility with callers that use the add/get_by_type API.
        """
        if isinstance(content, bytes):
            raw_content = content
            stored_content = content.decode("utf-8", errors="replace")
        elif isinstance(content, str):
            stored_content = content
            raw_content = content.encode("utf-8")
        else:
            stored_content = json.dumps(content, indent=2, default=str)
            raw_content = stored_content.encode("utf-8")

        artifact = ManagedArtifact(
            artifact_id=str(uuid.uuid4()),
            name=name,
            artifact_type=artifact_type,
            content=stored_content,
            created_by=created_by,
            tags=list(tags or []),
            checksum=hashlib.sha256(raw_content).hexdigest(),
        )
        self._artifacts.append(artifact)
        return artifact

    def get_by_type(self, artifact_type: str) -> List[ManagedArtifact]:
        """Return registered artifacts matching the requested type."""
        return [
            artifact
            for artifact in self._artifacts
            if artifact.artifact_type == artifact_type
        ]

    def create_project_structure(self, project_name: str) -> Path:
        """Create standard project directory structure.

        Args:
            project_name: Name of the project

        Returns:
            Path to project directory
        """
        project_dir = self.base_workspace / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        # Create standard directories
        dirs = ["code", "tests", "logs", "reflections", "docs"]
        for dir_name in dirs:
            (project_dir / dir_name).mkdir(exist_ok=True)

        # Create standard files if they don't exist
        self._create_file(project_dir / "plan.md", "# Project Plan\n\n")
        self._create_file(project_dir / "requirements.md", "# Requirements\n\n")
        self._create_file(project_dir / "architecture.md", "# Architecture\n\n")
        self._create_file(project_dir / "report.md", "# Project Report\n\n")
        self._create_file(project_dir / "metrics.json", "{}")
        self._create_file(project_dir / "benchmark.json", "{}")

        return project_dir

    def save_artifact(self, project_name: str, artifact_name: str, content: Any, category: str = "code") -> Path:
        """Save artifact to project.

        Args:
            project_name: Project name
            artifact_name: Artifact filename
            content: Artifact content (string or dict)
            category: Artifact category (code, tests, docs, logs, reflections)

        Returns:
            Path to saved artifact
        """
        project_dir = self.base_workspace / project_name
        category_dir = project_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = category_dir / artifact_name

        if isinstance(content, dict):
            content = json.dumps(content, indent=2)

        artifact_path.write_text(content, encoding="utf-8")
        return artifact_path

    def load_artifact(self, project_name: str, artifact_name: str, category: str = "code") -> Optional[str]:
        """Load artifact from project.

        Args:
            project_name: Project name
            artifact_name: Artifact filename
            category: Artifact category

        Returns:
            Artifact content or None if not found
        """
        artifact_path = self.base_workspace / project_name / category / artifact_name
        if artifact_path.exists():
            return artifact_path.read_text(encoding="utf-8")
        return None

    def save_metrics(self, project_name: str, metrics: Dict[str, Any]):
        """Save project metrics.

        Args:
            project_name: Project name
            metrics: Metrics dictionary
        """
        metrics["timestamp"] = datetime.now().isoformat()
        self.save_artifact(project_name, "metrics.json", metrics, category="")

    def load_metrics(self, project_name: str) -> Dict[str, Any]:
        """Load project metrics.

        Args:
            project_name: Project name

        Returns:
            Metrics dictionary
        """
        content = self.load_artifact(project_name, "metrics.json", category="")
        if content:
            try:
                return json.loads(content)
            except Exception:
                pass
        return {}

    def save_report(self, project_name: str, report: str):
        """Save project report.

        Args:
            project_name: Project name
            report: Report markdown content
        """
        self.save_artifact(project_name, "report.md", report, category="docs")

    def save_reflection(self, project_name: str, reflection: Dict[str, Any]):
        """Save reflection artifact.

        Args:
            project_name: Project name
            reflection: Reflection data
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reflection_{timestamp}.json"
        return self.save_artifact(project_name, filename, reflection, category="reflections")

    def list_artifacts(self, project_name: str, category: str = "") -> List[str]:
        """List all artifacts in project.

        Args:
            project_name: Project name
            category: Optional category filter

        Returns:
            List of artifact paths
        """
        project_dir = self.base_workspace / project_name
        if category:
            search_dir = project_dir / category
        else:
            search_dir = project_dir

        if not search_dir.exists():
            return []

        artifacts = []
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(project_dir)
                artifacts.append(str(rel_path))

        return sorted(artifacts)

    def get_project_path(self, project_name: str) -> Path:
        """Get project directory path.

        Args:
            project_name: Project name

        Returns:
            Path to project directory
        """
        return self.base_workspace / project_name

    def project_exists(self, project_name: str) -> bool:
        """Check if project exists.

        Args:
            project_name: Project name

        Returns:
            True if project exists
        """
        return self.get_project_path(project_name).exists()

    def archive_project(self, project_name: str) -> Optional[Path]:
        """Archive project directory.

        Args:
            project_name: Project name

        Returns:
            Path to archive or None if failed
        """
        import shutil

        project_dir = self.get_project_path(project_name)
        if not project_dir.exists():
            return None

        archive_path = self.base_workspace / f"{project_name}_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.move(str(project_dir), str(archive_path))
        return archive_path

    def _create_file(self, path: Path, content: str):
        """Create file if it doesn't exist."""
        if not path.exists():
            path.write_text(content, encoding="utf-8")
