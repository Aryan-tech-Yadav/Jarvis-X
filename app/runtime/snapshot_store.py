import copy
from datetime import datetime, timezone
from uuid import uuid4


class SnapshotStore:
    """In-memory snapshots; callers decide if/where durable storage is needed."""

    def __init__(self):
        self._snapshots = {}

    def save(self, payload, label="runtime"):
        snapshot_id = str(uuid4())
        self._snapshots[snapshot_id] = {
            "id": snapshot_id,
            "label": str(label),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": copy.deepcopy(payload),
        }
        return copy.deepcopy(self._snapshots[snapshot_id])

    def get(self, snapshot_id):
        item = self._snapshots.get(snapshot_id)
        return copy.deepcopy(item) if item else None

    def latest(self, label=None):
        items = [item for item in self._snapshots.values() if label is None or item["label"] == label]
        # Dict insertion order gives a deterministic "latest" result even
        # when two snapshots share the same clock resolution.
        return copy.deepcopy(items[-1]) if items else None
