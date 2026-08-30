"""Drift Detector for monitoring performance degradation and behavioral drift."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class DriftDetector:
    """Monitors metrics between releases or runs and detects performance, quality, or repair drift."""

    def __init__(self, tolerance_pct: float = 5.0):
        self.tolerance_pct = float(tolerance_pct)

    def detect_drift(
        self, current_metrics: Dict[str, float], baseline_metrics: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        warnings: List[str] = []

        for metric, current_val in current_metrics.items():
            if metric not in baseline_metrics:
                continue
            baseline_val = baseline_metrics[metric]
            if baseline_val == 0:
                continue

            # For time or memory metrics, higher is worse
            if "time" in metric.lower() or "memory" in metric.lower() or "tokens" in metric.lower():
                if current_val > baseline_val * (1.0 + self.tolerance_pct / 100.0):
                    pct_increase = ((current_val - baseline_val) / baseline_val) * 100.0
                    warnings.append(
                        f"⚠ {metric.replace('_', ' ').title()} regressed by {pct_increase:.1f}% ({baseline_val:.2f} → {current_val:.2f})"
                    )
            # For score or coverage metrics, lower is worse
            else:
                if current_val < baseline_val * (1.0 - self.tolerance_pct / 100.0):
                    pct_drop = ((baseline_val - current_val) / baseline_val) * 100.0
                    warnings.append(
                        f"⚠ {metric.replace('_', ' ').title()} dropped by {pct_drop:.1f}% ({baseline_val:.2f} → {current_val:.2f})"
                    )

        has_drift = len(warnings) > 0
        return has_drift, warnings
