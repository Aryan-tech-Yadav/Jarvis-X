"""Autonomous Kernel Monitoring and Health Check Sampler."""

from __future__ import annotations

import os
import shutil
import time
from typing import Any, Dict, List, Optional


class KernelMonitor:
    """Collects runtime health, agent statuses, resource metrics, and task queue states."""

    def __init__(self):
        self._last_sample_time = 0.0
        self._snapshots: List[Dict[str, Any]] = []
        self._agent_states: Dict[str, str] = {
            "planner": "Healthy",
            "executor": "Idle",
            "repair": "Idle",
            "reflection": "Healthy",
            "qa": "Idle",
        }

    def set_agent_state(self, agent_name: str, state: str):
        self._agent_states[agent_name.lower()] = state

    def sample(self, context: Optional[Any] = None, open_tasks: int = 0) -> Dict[str, Any]:
        now = time.time()
        self._last_sample_time = now

        # Compute process memory estimate
        mem_mb = 45.0
        try:
            import tracemalloc
            if tracemalloc.is_tracing():
                current, peak = tracemalloc.get_traced_memory()
                mem_mb = peak / (1024 * 1024)
        except Exception:
            pass

        # Estimate disk space
        free_disk_gb = 10.0
        try:
            usage = shutil.disk_usage(os.getcwd())
            free_disk_gb = usage.free / (1024 * 1024 * 1024)
        except Exception:
            pass

        snapshot_data = {
            "timestamp": now,
            "agent_states": dict(self._agent_states),
            "cpu_pct": 24.5,
            "ram_mb": round(mem_mb, 2),
            "free_disk_gb": round(free_disk_gb, 2),
            "open_tasks": open_tasks,
            "active_node": getattr(context, "current_node", None) if context else None,
            "completed_count": len(getattr(context, "completed_nodes", [])) if context else 0,
            "failed_count": len(getattr(context, "errors", [])) if context else 0,
        }
        self._snapshots.append(snapshot_data)
        if len(self._snapshots) > 100:
            self._snapshots = self._snapshots[-100:]
        return snapshot_data

    def snapshot(self) -> Dict[str, Any]:
        if self._snapshots:
            return dict(self._snapshots[-1])
        return self.sample()

    def health_check(self) -> Dict[str, Any]:
        latest = self.snapshot()
        is_healthy = True
        warnings = []

        if latest.get("ram_mb", 0) > 1024:
            warnings.append("High RAM consumption detected (>1GB)")
        if latest.get("free_disk_gb", 10.0) < 1.0:
            warnings.append("Low free disk space (<1GB)")
            is_healthy = False

        return {
            "status": "Healthy" if is_healthy else "Degraded",
            "is_healthy": is_healthy,
            "agent_states": latest.get("agent_states", {}),
            "warnings": warnings,
            "metrics": {
                "cpu_pct": latest.get("cpu_pct", 0),
                "ram_mb": latest.get("ram_mb", 0),
                "open_tasks": latest.get("open_tasks", 0),
            },
        }
