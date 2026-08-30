from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Workspace:
    root: Path

    @property
    def projects_path(self):
        return self.root / "projects"

    @property
    def archives_path(self):
        return self.root / "archives"

    @property
    def trash_path(self):
        return self.root / ".trash"

    @property
    def registry_path(self):
        return self.root / "workspace.json"
