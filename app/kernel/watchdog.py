"""Kernel Watchdog for timeout enforcement, deadlock detection, and worker resilience."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Set


class KernelWatchdog:
    """Monitors task execution timeouts, detect deadlocks, and recovers stalled node workers."""

    def __init__(self, default_timeout_sec: float = 30.0):
        self.default_timeout_sec = float(default_timeout_sec)
        self._active_timers: Dict[str, float] = {}  # node_id -> start_time

    def start_node(self, node_id: str):
        self._active_timers[str(node_id)] = time.time()

    def finish_node(self, node_id: str):
        self._active_timers.pop(str(node_id), None)

    def check_timeouts(self, custom_timeouts: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        now = time.time()
        timeouts = custom_timeouts or {}
        stalled: List[Dict[str, Any]] = []

        for node_id, start_t in list(self._active_timers.items()):
            limit = timeouts.get(node_id, self.default_timeout_sec)
            elapsed = now - start_t
            if elapsed > limit:
                stalled.append({
                    "node_id": node_id,
                    "elapsed_sec": round(elapsed, 2),
                    "limit_sec": limit,
                    "reason": f"Node '{node_id}' exceeded timeout limit ({elapsed:.1f}s > {limit:.1f}s)",
                })

        return stalled

    def detect_deadlock(self, graph_nodes: Dict[str, Any], completed_nodes: Set[str]) -> Optional[List[str]]:
        unresolved = [n for n in graph_nodes if n not in completed_nodes]
        if not unresolved:
            return None

        # Check if every unresolved node has at least one unmet dependency that is also unresolved
        deadlocked = True
        for n_id in unresolved:
            deps = graph_nodes[n_id].get("dependencies", set())
            if isinstance(deps, (list, tuple)):
                deps = set(deps)
            if not deps or deps.issubset(completed_nodes):
                deadlocked = False
                break

        if deadlocked and len(unresolved) > 0:
            return unresolved
        return None
