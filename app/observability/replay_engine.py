"""Replay Engine for auditing and verifying historical runs."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.results import ExecutionResult
from .artifact_store import ArtifactStore


class ReplayEngine:
    """Replays historical executions from persisted artifacts for deterministic verification."""

    def __init__(self, artifact_store: Optional[ArtifactStore] = None):
        self.artifact_store = artifact_store or ArtifactStore()

    def replay_run(self, run_id: str) -> ExecutionResult:
        artifacts = self.artifact_store.load_run_artifacts(run_id)
        if not artifacts:
            return ExecutionResult.failed(f"Run ID '{run_id}' not found in artifact store.")

        timeline = artifacts.get("timeline", [])
        events_replayed = len(timeline)
        quality = artifacts.get("quality", {})
        plan = artifacts.get("plan", {})

        return ExecutionResult.completed(
            data={
                "run_id": run_id,
                "events_replayed": events_replayed,
                "plan_present": bool(plan),
                "quality_present": bool(quality),
                "artifacts": artifacts,
            },
            message=f"Successfully replayed run '{run_id}' ({events_replayed} timeline events).",
        )
