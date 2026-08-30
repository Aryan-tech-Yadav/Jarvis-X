"""Benchmark Validator, Historical Trend Tracking, and Regression Detection."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class BenchmarkValidator:
    """Tracks historical benchmark runs, generates trend graphs, and enforces quality gates."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir else (Path.cwd() / "knowledge")
        self.benchmarks_dir = self.knowledge_dir / "benchmarks"
        self.benchmarks_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.benchmarks_dir / "benchmark_history.json"
        self._history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            self.history_file.write_text(json.dumps(self._history, indent=2), encoding="utf-8")
        except Exception:
            pass

    def record_run(
        self,
        version: str,
        planning_score: float,
        execution_score: float,
        repair_score: float,
        coverage: float,
        security: float,
        performance: float,
        overall_grade: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        overall_score = (
            planning_score * 0.15
            + execution_score * 0.20
            + repair_score * 0.15
            + coverage * 0.20
            + security * 0.15
            + performance * 0.15
        )

        entry = {
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "planning_score": round(float(planning_score), 2),
            "execution_score": round(float(execution_score), 2),
            "repair_score": round(float(repair_score), 2),
            "coverage": round(float(coverage), 2),
            "security": round(float(security), 2),
            "performance": round(float(performance), 2),
            "overall_score": round(float(overall_score), 2),
            "overall_grade": overall_grade,
            "metadata": metadata or {},
        }
        self._history.append(entry)
        self._save_history()
        return entry

    def compare_with_baseline(self, current_run: Dict[str, Any]) -> Tuple[bool, List[str]]:
        if not self._history or len(self._history) < 2:
            return True, ["Baseline established."]

        previous_run = self._history[-2] if self._history[-1] == current_run else self._history[-1]
        regressions: List[str] = []

        for metric in ["planning_score", "execution_score", "repair_score", "coverage", "security", "performance", "overall_score"]:
            prev_val = float(previous_run.get(metric, 0.0))
            curr_val = float(current_run.get(metric, 0.0))
            if curr_val < prev_val - 3.0:
                regressions.append(
                    f"Regression in '{metric}': dropped from {prev_val:.1f} to {curr_val:.1f} (-{prev_val - curr_val:.1f})"
                )

        passed = len(regressions) == 0
        return passed, regressions

    def generate_trend_graph(self) -> str:
        if not self._history:
            return "No benchmark history recorded."

        lines = [
            "### 📈 Benchmark Quality Evolution Trend",
            "```text",
        ]

        for i, entry in enumerate(self._history):
            ver = entry.get("version", f"run_{i+1}")
            score = entry.get("overall_score", 0.0)
            bar_len = int(score / 4.0)
            bar = "█" * bar_len + "░" * (25 - bar_len)
            lines.append(f"{ver:<8} │ {bar} │ {score:>5.1f} [{entry.get('overall_grade', 'N/A')}]")
            if i < len(self._history) - 1:
                lines.append("         │")

        lines.extend([
            "```",
        ])
        return "\n".join(lines)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
