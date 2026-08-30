"""Improvement engine.

Compares project versions to measure objective improvement:
  - runtime delta
  - code quality delta
  - coverage delta
  - repair count delta

Example output:
  Runtime       -18%
  Code Quality  +7
  Coverage      +5%
  Repair        -40%
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ImprovementEngine:
    """Compare two project executions and compute deltas."""

    def compare(self, baseline: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
        """Compare baseline vs current metrics.

        Returns a dict with:
          - deltas for numeric fields
          - qualitative notes for significant changes
        """
        keys = ["duration", "files_generated", "tests_count", "repair_count",
                "warnings", "errors", "overall_score", "coverage", "quality"]
        deltas: Dict[str, Any] = {}
        notes: List[str] = []

        for key in keys:
            b = self._safe_float(baseline.get(key))
            c = self._safe_float(current.get(key))
            if b == 0.0 and c == 0.0:
                continue
            if b == 0.0:
                delta = c
                notes.append(f"{key} introduced with value {c}")
            else:
                delta = c - b
                if delta == 0.0:
                    continue
                pct = (delta / abs(b)) * 100 if b != 0 else 0.0
                deltas[f"{key}_delta"] = round(delta, 3)
                deltas[f"{key}_pct"] = round(pct, 2)
                if key == "duration" and pct < -5:
                    notes.append(f"Runtime improved by {abs(pct):.1f}%")
                elif key == "repair_count" and delta < 0:
                    notes.append(f"Repairs reduced by {abs(delta):.0f}")
                elif key == "overall_score" and delta > 0:
                    notes.append(f"Quality improved by +{delta:.1f}")

        return {
            "deltas": deltas,
            "notes": notes,
            "baseline": baseline,
            "current": current,
        }

    def _safe_float(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
