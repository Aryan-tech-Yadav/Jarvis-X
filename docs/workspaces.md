# Workspaces and project management

`WorkspaceManager` persists multiple isolated Jarvis-X projects below one chosen
workspace root. Each project keeps its own planning/execution/repair state,
memory, timeline, metrics, reports, and snapshots.

```python
from app.workspace import WorkspaceManager

manager = WorkspaceManager("workspaces/team-a")
manager.create_workspace()
project = manager.create_project("Hospital Management System")
snapshot_id = manager.snapshot_project(project.project_id)

# Project deletion is recoverable: it moves only this project to the workspace's
# `.trash` directory. Restore returns it to the active project area.
manager.archive_project(project.project_id)
manager.restore_project(project.project_id)
```

The workspace can run a supplied `GenerationPipeline`; it snapshots the project
before the run and persists the returned timeline, metrics, reports, and status.

```powershell
python -m app.release.cli workspace create workspaces\team-a
python -m app.release.cli workspace project-create workspaces\team-a "Notes API"
python -m app.release.cli workspace list workspaces\team-a
python -m app.release.cli workspace doctor workspaces\team-a
```
