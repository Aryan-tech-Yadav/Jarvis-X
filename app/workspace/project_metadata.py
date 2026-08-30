from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ProjectMetadata:
    project_id: str
    name: str
    description: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    status: str = "created"
    location: str = "active"

    def to_dict(self):
        return {
            "id": self.project_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "status": self.status,
            "location": self.location,
        }

    @classmethod
    def from_dict(cls, value):
        return cls(value["id"], value["name"], value.get("description", ""),
                   value.get("created_at", _now()), value.get("updated_at", _now()),
                   value.get("status", "created"), value.get("location", "active"))
