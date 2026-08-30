"""Version Intelligence Engine for comparing releases, tracking improvements, and detecting drift."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class VersionEngine:
    """Tracks metrics across releases (v0.8 -> v0.9 -> v1.0) and detects performance or quality drift."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir else (Path.cwd() / "knowledge")
        self.versions_dir = self.knowledge_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.versions_dir / "version_history.json"
        self._history: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if not self.store_file.exists():
            return []
        try:
            return json.loads(self.store_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self):
        try:
            self.store_file.write_text(json.dumps(self._history, indent=2), encoding="utf-8")
        except Exception:
            pass

    def record_version(
        self,
        version: str,
        planning_score: float,
        execution_score: float,
        qa_score: float,
        repair_score: float,
        performance_score: float,
        coverage_pct: float,
        overall_score: Optional[float] = None,
        notes: str = "",
    ) -> Dict[str, Any]:
        overall = overall_score if overall_score is not None else (
            planning_score * 0.20
            + execution_score * 0.20
            + qa_score * 0.20
            + repair_score * 0.15
            + performance_score * 0.15
            + (coverage_pct * 0.10)
        )

        entry = {
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "planning_score": round(float(planning_score), 2),
            "execution_score": round(float(execution_score), 2),
            "qa_score": round(float(qa_score), 2),
            "repair_score": round(float(repair_score), 2),
            "performance_score": round(float(performance_score), 2),
            "coverage_pct": round(float(coverage_pct), 2),
            "overall_score": round(float(overall), 2),
            "notes": notes,
        }

        # Update if exists, else append
        for idx, item in enumerate(self._history):
            if item.get("version") == version:
                self._history[idx] = entry
                self._save()
                return entry

        self._history.append(entry)
        self._save()
        return entry

    def compare_releases(self, current_version: str, baseline_version: Optional[str] = None) -> Dict[str, Any]:
        curr = next((v for v in reversed(self._history) if v.get("version") == current_version), None)
        if not curr:
            return {"error": f"Version '{current_version}' not found"}

        if baseline_version:
            base = next((v for v in self._history if v.get("version") == baseline_version), None)
        else:
            # Pick the release right before current
            curr_idx = next((i for i, v in enumerate(self._history) if v.get("version") == current_version), 0)
            base = self._history[curr_idx - 1] if curr_idx > 0 else None

        if not base:
            return {
                "version": current_version,
                "baseline": "None (Initial Release)",
                "deltas": {},
                "regressions": [],
                "improvements": ["Baseline version established."],
            }

        deltas = {}
        regressions = []
        improvements = []

        for metric in ["planning_score", "execution_score", "qa_score", "repair_score", "performance_score", "coverage_pct", "overall_score"]:
            c_val = float(curr.get(metric, 0.0))
            b_val = float(base.get(metric, 0.0))
            diff = c_val - b_val
            deltas[metric] = round(diff, 2)

            if diff < -2.0:
                regressions.append(f"⚠ {metric.replace('_', ' ').title()} dropped by {abs(diff):.1f} pts ({b_val:.1f} → {c_val:.1f})")
            elif diff > 2.0:
                improvements.append(f"🚀 {metric.replace('_', ' ').title()} improved by {diff:.1f} pts ({b_val:.1f} → {c_val:.1f})")

        return {
            "version": current_version,
            "baseline": base.get("version"),
            "deltas": deltas,
            "regressions": regressions,
            "improvements": improvements,
            "net_growth_pct": round(deltas.get("overall_score", 0.0), 2),
        }

    def get_version_trend_summary(self) -> str:
        if not self._history:
            return "No version history available."

        lines = ["### 📈 Version Evolution Trajectory", "```text"]
        for entry in self._history:
            ver = entry.get("version", "v?")
            score = entry.get("overall_score", 0.0)
            bar = "█" * int(score / 5.0) + "░" * (20 - int(score / 5.0))
            lines.append(f"{ver:<8} │ {bar} │ {score:>5.1f}%")
        lines.append("```")
        return "\n".join(lines)
