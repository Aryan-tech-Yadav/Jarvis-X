"""Artifact Store for persisting and retrieving immutable run bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


class ArtifactStore:
    """Saves requirements, architecture, plan, timeline, metrics, quality, and release bundles."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir).resolve() if base_dir else (Path.cwd() / "artifacts")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_run_artifacts(
        self,
        run_id: str,
        requirements: Optional[Dict[str, Any]] = None,
        architecture: Optional[Dict[str, Any]] = None,
        plan: Optional[Dict[str, Any]] = None,
        timeline: Optional[List[Any]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        quality: Optional[Dict[str, Any]] = None,
        release: Optional[Dict[str, Any]] = None,
    ) -> Path:
        run_dir = self.base_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        artifacts = {
            "requirements.json": requirements or {},
            "architecture.json": architecture or {},
            "plan.json": plan or {},
            "timeline.json": timeline or [],
            "metrics.json": metrics or {},
            "quality.json": quality or {},
            "release.json": release or {},
        }

        for filename, data in artifacts.items():
            try:
                (run_dir / filename).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
            except Exception:
                pass

        return run_dir

    def load_run_artifacts(self, run_id: str) -> Optional[Dict[str, Any]]:
        run_dir = self.base_dir / run_id
        if not run_dir.exists():
            return None

        result = {"run_id": run_id}
        for f in run_dir.glob("*.json"):
            try:
                result[f.stem] = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                result[f.stem] = {}

        return result
