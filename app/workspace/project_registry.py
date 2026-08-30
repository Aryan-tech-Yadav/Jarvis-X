class ProjectRegistry:
    def __init__(self, entries=None, active_project_id=None):
        self._entries = dict(entries or {})
        self.active_project_id = active_project_id

    def register(self, project):
        if project.project_id in self._entries:
            raise ValueError("Project already registered: " + project.project_id)
        self._entries[project.project_id] = project.metadata.to_dict()
        self.active_project_id = project.project_id
        return project

    def update(self, project):
        if project.project_id not in self._entries:
            raise KeyError("Unknown project: " + project.project_id)
        self._entries[project.project_id] = project.metadata.to_dict()
        return project

    def get(self, project_id):
        return dict(self._entries[project_id]) if project_id in self._entries else None

    def open(self, project_id):
        if project_id not in self._entries:
            raise KeyError("Unknown project: " + str(project_id))
        self.active_project_id = project_id
        return self.get(project_id)

    def entries(self, include_deleted=False):
        values = [dict(value) for value in self._entries.values()]
        return values if include_deleted else [value for value in values if value.get("location") != "trash"]

    def to_dict(self):
        return {"active_project_id": self.active_project_id, "projects": self._entries}

    @classmethod
    def from_dict(cls, value):
        return cls(value.get("projects", {}), value.get("active_project_id"))
