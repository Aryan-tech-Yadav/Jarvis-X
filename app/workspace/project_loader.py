import json
from pathlib import Path

from .project import WorkspaceProject


class ProjectLoader:
    PROJECT_FILE = "project.json"

    def project_path(self, workspace, project_id, location="active"):
        roots = {"active": workspace.projects_path, "archive": workspace.archives_path, "trash": workspace.trash_path}
        if location not in roots:
            raise ValueError("Unsupported project location: " + str(location))
        return roots[location] / str(project_id)

    def save(self, workspace, project):
        path = self.project_path(workspace, project.project_id, project.metadata.location)
        path.mkdir(parents=True, exist_ok=True)
        self._write(path / self.PROJECT_FILE, project.to_dict())
        return path

    def load(self, workspace, project_id, location="active"):
        path = self.project_path(workspace, project_id, location) / self.PROJECT_FILE
        if not path.is_file():
            raise FileNotFoundError("Project data not found: " + str(project_id))
        with path.open("r", encoding="utf-8") as file:
            return WorkspaceProject.from_dict(json.load(file))

    def snapshot(self, workspace, project, context=None):
        from datetime import datetime, timezone
        from uuid import uuid4

        project_root = self.project_path(workspace, project.project_id, project.metadata.location)
        snapshot_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f") + "-" + str(uuid4())[:8]
        snapshot = project_root / "snapshots" / snapshot_id
        snapshot.mkdir(parents=True, exist_ok=False)
        self._write(snapshot / "project.json", project.to_dict())
        self._write(snapshot / "plan.json", project.planner_state)
        self._write(snapshot / "memory.json", project.memory)
        self._write(snapshot / "timeline.json", project.timeline)
        self._write(snapshot / "metrics.json", project.metrics)
        self._write(snapshot / "context.json", context.as_dict() if hasattr(context, "as_dict") else context or {})
        return snapshot_id

    def restore_snapshot(self, workspace, project_id, snapshot_id, location="active"):
        snapshot = self.project_path(workspace, project_id, location) / "snapshots" / str(snapshot_id) / "project.json"
        if not snapshot.is_file():
            raise FileNotFoundError("Snapshot not found: " + str(snapshot_id))
        with snapshot.open("r", encoding="utf-8") as file:
            return WorkspaceProject.from_dict(json.load(file))

    @staticmethod
    def _write(path, value):
        with Path(path).open("w", encoding="utf-8") as file:
            json.dump(value, file, indent=2, sort_keys=True, default=str)
