import json
import shutil
from pathlib import Path
from uuid import uuid4

from app.events.event_bus import EventBus

from .project import WorkspaceProject
from .project_loader import ProjectLoader
from .project_metadata import ProjectMetadata
from .project_registry import ProjectRegistry
from .workspace import Workspace
from .workspace_events import (PROJECT_ARCHIVED, PROJECT_CREATED, PROJECT_DELETED,
                               PROJECT_OPENED, PROJECT_RESTORED)
from .workspace_metrics import WorkspaceMetrics


class WorkspaceManager:
    """Owns persisted workspace metadata and recoverable project lifecycle actions."""

    def __init__(self, root, loader=None, event_bus=None, metrics=None):
        self.workspace = Workspace(Path(root).expanduser().resolve())
        self.loader = loader or ProjectLoader()
        self.events = event_bus or EventBus()
        self.metrics_engine = metrics or WorkspaceMetrics()
        self.registry = ProjectRegistry()

    def create_workspace(self):
        for path in (self.workspace.root, self.workspace.projects_path, self.workspace.archives_path, self.workspace.trash_path):
            path.mkdir(parents=True, exist_ok=True)
        if not self.workspace.registry_path.exists():
            self._save_registry()
        else:
            self._load_registry()
        return self.workspace

    def load_workspace(self):
        if not self.workspace.registry_path.is_file():
            raise FileNotFoundError("Workspace does not exist: " + str(self.workspace.root))
        self._load_registry()
        return self.workspace

    def create_project(self, name, description=""):
        self._require_workspace()
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Project name cannot be empty")
        project_id = self._project_id(name)
        project = WorkspaceProject(ProjectMetadata(project_id, name.strip(), str(description or "")))
        self.loader.save(self.workspace, project)
        self.registry.register(project)
        self._save_registry()
        self._publish(PROJECT_CREATED, project)
        return project

    def open_project(self, project_id):
        self._require_workspace()
        metadata = self.registry.open(project_id)
        if metadata["location"] != "active":
            raise ValueError("Project is not active; restore it before opening")
        project = self.loader.load(self.workspace, project_id, metadata["location"])
        # Opening is an access event, not an execution-state transition. A
        # completed project must stay completed after a later inspection.
        project.touch()
        self.save_project(project)
        self._publish(PROJECT_OPENED, project)
        return project

    def save_project(self, project):
        self._require_workspace()
        project.touch()
        self.loader.save(self.workspace, project)
        self.registry.update(project)
        self._save_registry()
        return project

    def list_projects(self, include_deleted=False):
        self._require_workspace()
        return self.registry.entries(include_deleted)

    def archive_project(self, project_id):
        return self._move(project_id, "archive", PROJECT_ARCHIVED, "archived")

    def restore_project(self, project_id):
        metadata = self._metadata(project_id)
        if metadata["location"] not in {"archive", "trash"}:
            raise ValueError("Only archived or deleted projects can be restored")
        return self._move(project_id, "active", PROJECT_RESTORED, "open")

    def delete_project(self, project_id):
        """Recoverably delete a project by moving it to this workspace's trash."""
        return self._move(project_id, "trash", PROJECT_DELETED, "deleted")

    def snapshot_project(self, project_id, context=None):
        metadata = self._metadata(project_id)
        project = self.loader.load(self.workspace, project_id, metadata["location"])
        return self.loader.snapshot(self.workspace, project, context)

    def restore_snapshot(self, project_id, snapshot_id):
        metadata = self._metadata(project_id)
        if metadata["location"] != "active":
            raise ValueError("Restore a project before restoring its snapshot")
        project = self.loader.restore_snapshot(self.workspace, project_id, snapshot_id)
        project.metadata.location = "active"
        self.save_project(project)
        self._publish(PROJECT_RESTORED, project, {"snapshot_id": snapshot_id})
        return project

    def run_pipeline(self, project_id, pipeline):
        """Snapshot, run, and persist a pipeline without coupling workspace to its stages."""
        project = self.open_project(project_id)
        from app.pipeline.pipeline_context import PipelineContext

        goal = project.metadata.description or project.name
        context = PipelineContext(goal, project_path=str(self.loader.project_path(self.workspace, project_id)))
        context.memory.update(project.memory)
        snapshot_id = self.snapshot_project(project_id, context)
        result = pipeline.run(context.goal, context)
        project.timeline = list(context.timeline)
        project.memory = dict(context.memory)
        project.metrics = dict(context.metrics)
        project.reports = [*project.reports, *context.artifacts]
        project.executor_state = {"pipeline_status": result.status, "snapshot_id": snapshot_id}
        project.touch("completed" if result.success else result.status)
        self.save_project(project)
        return result

    def metrics(self):
        projects = []
        for metadata in self.registry.entries():
            projects.append(self.loader.load(self.workspace, metadata["id"], metadata["location"]))
        return self.metrics_engine.calculate(projects)

    def _move(self, project_id, destination, event_type, status):
        self._require_workspace()
        metadata = self._metadata(project_id)
        source_location = metadata["location"]
        if source_location == destination:
            return self.loader.load(self.workspace, project_id, source_location)
        source = self.loader.project_path(self.workspace, project_id, source_location)
        target = self.loader.project_path(self.workspace, project_id, destination)
        if not source.is_dir():
            raise FileNotFoundError("Project data not found: " + project_id)
        if target.exists():
            raise ValueError("Destination project already exists: " + project_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        project = self.loader.load(self.workspace, project_id, destination)
        project.metadata.location = destination
        project.touch(status)
        self.loader.save(self.workspace, project)
        self.registry.update(project)
        if destination != "active" and self.registry.active_project_id == project_id:
            self.registry.active_project_id = None
        self._save_registry()
        self._publish(event_type, project)
        return project

    def _metadata(self, project_id):
        self._require_workspace()
        metadata = self.registry.get(project_id)
        if metadata is None:
            raise KeyError("Unknown project: " + str(project_id))
        return metadata

    def _require_workspace(self):
        if not self.workspace.registry_path.is_file():
            raise RuntimeError("Create or load the workspace before using projects")

    def _save_registry(self):
        with self.workspace.registry_path.open("w", encoding="utf-8") as file:
            json.dump(self.registry.to_dict(), file, indent=2, sort_keys=True)

    def _load_registry(self):
        with self.workspace.registry_path.open("r", encoding="utf-8") as file:
            self.registry = ProjectRegistry.from_dict(json.load(file))

    def _publish(self, event_type, project, extra=None):
        payload = {"project_id": project.project_id, "name": project.name, "status": project.status}
        payload.update(extra or {})
        return self.events.publish(event_type, payload)

    def _project_id(self, name):
        slug = "".join(character if character.isalnum() else "-" for character in name.casefold()).strip("-") or "project"
        slug = "-".join(part for part in slug.split("-") if part)
        return slug[:48] + "-" + str(uuid4())[:8]
