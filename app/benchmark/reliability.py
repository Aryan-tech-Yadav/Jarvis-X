"""Durable reliability records for repeated autonomy benchmark runs."""

from __future__ import annotations

import json
import os
import uuid
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


FAILURE_CLASSES = frozenset(
    {"timeout", "crash", "validation", "recovery", "intervention", "unknown"}
)


def classify_failure(
    error: Optional[str] = None,
    *,
    recovered: bool = False,
    manual_intervention: float = 0.0,
) -> Optional[str]:
    """Classify an unsuccessful run using explicit, observable run metadata."""
    if recovered:
        return "recovery"
    if manual_intervention > 0:
        return "intervention"
    if not error:
        return None
    lowered = error.casefold()
    if "timeout" in lowered or "timed out" in lowered:
        return "timeout"
    if "valid" in lowered or "schema" in lowered:
        return "validation"
    if "crash" in lowered or "exception" in lowered:
        return "crash"
    return "unknown"


@dataclass(frozen=True)
class ReliabilityRun:
    benchmark_id: str
    success: bool
    duration_seconds: float = 0.0
    manual_intervention: float = 0.0
    recovered: bool = False
    error: Optional[str] = None
    failure_class: Optional[str] = None
    run_id: str = ""
    recorded_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id or f"run-{uuid.uuid4().hex[:12]}",
            "recorded_at": self.recorded_at or datetime.now(timezone.utc).isoformat(),
            "benchmark_id": self.benchmark_id,
            "success": self.success,
            "duration_seconds": max(0.0, float(self.duration_seconds)),
            "manual_intervention": max(0.0, min(1.0, float(self.manual_intervention))),
            "recovered": self.recovered,
            "error": self.error,
            "failure_class": self.failure_class
            or classify_failure(
                self.error,
                recovered=self.recovered,
                manual_intervention=self.manual_intervention,
            ),
        }


class ReliabilityLedger:
    """Append-only JSON ledger for repeatable benchmark and recovery analysis."""

    def __init__(self, path: Optional[str] = None):
        self.path = path
        self._runs: List[Dict[str, Any]] = self._load() if path else []

    def record(self, run: ReliabilityRun | Dict[str, Any]) -> Dict[str, Any]:
        entry = run.to_dict() if isinstance(run, ReliabilityRun) else self._normalize(run)
        self._runs.append(entry)
        if self.path:
            self._save()
        return deepcopy(entry)

    def runs(self, benchmark_id: Optional[str] = None) -> List[Dict[str, Any]]:
        selected = self._runs
        if benchmark_id is not None:
            selected = [run for run in selected if run["benchmark_id"] == benchmark_id]
        return deepcopy(selected)

    def summary(self, benchmark_ids: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        allowed = set(benchmark_ids) if benchmark_ids is not None else None
        runs = [
            run for run in self._runs
            if allowed is None or run["benchmark_id"] in allowed
        ]
        total = len(runs)
        successful = sum(bool(run["success"]) for run in runs)
        recovered = sum(bool(run["recovered"]) for run in runs)
        failures: Dict[str, int] = {}
        for run in runs:
            failure_class = run.get("failure_class")
            if not run["success"] and failure_class:
                failures[failure_class] = failures.get(failure_class, 0) + 1
        return {
            "kind": "reliability_summary",
            "total_runs": total,
            "successful_runs": successful,
            "success_rate": round(successful / total, 4) if total else 0.0,
            "recovery_rate": round(recovered / total, 4) if total else 0.0,
            "failure_classes": failures,
        }

    def _normalize(self, run: Dict[str, Any]) -> Dict[str, Any]:
        benchmark_id = str(run.get("benchmark_id", "")).strip()
        if not benchmark_id:
            raise ValueError("Reliability run requires benchmark_id")
        failure_class = run.get("failure_class")
        if failure_class is not None and failure_class not in FAILURE_CLASSES:
            raise ValueError(f"Unsupported failure class: {failure_class}")
        return ReliabilityRun(
            benchmark_id=benchmark_id,
            success=bool(run.get("success", False)),
            duration_seconds=float(run.get("duration_seconds", 0.0)),
            manual_intervention=float(run.get("manual_intervention", 0.0)),
            recovered=bool(run.get("recovered", False)),
            error=run.get("error"),
            failure_class=failure_class,
            run_id=str(run.get("run_id", "")),
            recorded_at=str(run.get("recorded_at", "")),
        ).to_dict()

    def _load(self) -> List[Dict[str, Any]]:
        if not self.path or not os.path.isfile(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as source:
                payload = json.load(source)
        except (OSError, json.JSONDecodeError):
            return []
        return payload if isinstance(payload, list) else []

    def _save(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(directory, exist_ok=True)
        temporary = self.path + ".tmp"
        with open(temporary, "w", encoding="utf-8") as destination:
            json.dump(self._runs, destination, indent=2, sort_keys=True)
        os.replace(temporary, self.path)
