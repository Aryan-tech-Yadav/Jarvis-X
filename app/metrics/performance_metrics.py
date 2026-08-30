"""Performance and resource utilization metrics.

Tracks runtime performance metrics:
  - CPU usage
  - memory consumption
  - I/O operations
  - network calls
  - execution time per phase
  - bottleneck identification

Example output:
  CPU Usage          45.2%
  Memory Peak        512 MB
  I/O Operations      1,245
  Network Calls       89
  Bottleneck          database_phase
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class PhasePerformance:
    """Performance metrics for a single phase."""

    phase: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    io_operations: int = 0
    network_calls: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "duration": round(self.duration, 3),
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_mb": round(self.memory_mb, 2),
            "io_operations": self.io_operations,
            "network_calls": self.network_calls,
            "metadata": dict(self.metadata),
        }


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""

    timestamp: float = 0.0
    cpu_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    network_recv_bytes: int = 0
    network_sent_bytes: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "cpu_percent": round(self.cpu_percent, 2),
            "memory_used_mb": round(self.memory_used_mb, 2),
            "memory_available_mb": round(self.memory_available_mb, 2),
            "disk_read_bytes": self.disk_read_bytes,
            "disk_write_bytes": self.disk_write_bytes,
            "network_recv_bytes": self.network_recv_bytes,
            "network_sent_bytes": self.network_sent_bytes,
        }


@dataclass
class PerformanceReport:
    """Aggregated performance report."""

    total_duration: float = 0.0
    peak_cpu: float = 0.0
    avg_cpu: float = 0.0
    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    total_io_operations: int = 0
    total_network_calls: int = 0
    phases: List[PhasePerformance] = field(default_factory=list)
    bottleneck_phase: str = ""
    slowest_phase: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_duration": round(self.total_duration, 3),
            "peak_cpu": round(self.peak_cpu, 2),
            "avg_cpu": round(self.avg_cpu, 2),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "avg_memory_mb": round(self.avg_memory_mb, 2),
            "total_io_operations": self.total_io_operations,
            "total_network_calls": self.total_network_calls,
            "phases": [p.to_dict() for p in self.phases],
            "bottleneck_phase": self.bottleneck_phase,
            "slowest_phase": self.slowest_phase,
        }


class PerformanceTracker:
    """Track runtime performance and resource utilization."""

    def __init__(self, performance_path: str = os.path.join("data", "performance.json")):
        self.performance_path = performance_path
        self._phase_starts: Dict[str, float] = {}
        self._phases: List[PhasePerformance] = []
        self._snapshots: List[ResourceSnapshot] = []
        self._reports: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.isfile(self.performance_path):
            try:
                with open(self.performance_path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if isinstance(raw, list):
                    self._reports = raw
            except (OSError, json.JSONDecodeError, TypeError):
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.performance_path), exist_ok=True)
        with open(self.performance_path, "w", encoding="utf-8") as f:
            json.dump(self._reports, f, indent=2, default=str)

    def start_phase(self, phase: str) -> float:
        """Start timing a phase. Returns the start timestamp."""
        now = time.perf_counter()
        self._phase_starts[phase] = now
        return now

    def end_phase(self, phase: str, metadata: Optional[Dict[str, Any]] = None) -> PhasePerformance:
        """End timing a phase and record metrics."""
        end_time = time.perf_counter()
        start_time = self._phase_starts.get(phase, end_time)
        duration = end_time - start_time

        snapshot = self._capture_snapshot()

        phase_perf = PhasePerformance(
            phase=phase,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            cpu_percent=snapshot.cpu_percent,
            memory_mb=snapshot.memory_used_mb,
            io_operations=snapshot.disk_read_bytes + snapshot.disk_write_bytes,
            network_calls=snapshot.network_recv_bytes + snapshot.network_sent_bytes,
            metadata=metadata or {},
        )
        self._phases.append(phase_perf)
        return phase_perf

    def timed_phase(self, phase: str):
        """Context manager for timing a phase."""
        return _PhaseTimer(self, phase)

    def record_snapshot(self) -> ResourceSnapshot:
        """Record a resource snapshot."""
        snapshot = self._capture_snapshot()
        self._snapshots.append(snapshot)
        return snapshot

    def _capture_snapshot(self) -> ResourceSnapshot:
        """Capture current system resource usage."""
        snapshot = ResourceSnapshot(timestamp=time.time())
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            disk = psutil.disk_io_counters()
            net = psutil.net_io_counters()

            snapshot.cpu_percent = cpu
            snapshot.memory_used_mb = mem.used / (1024 * 1024)
            snapshot.memory_available_mb = mem.available / (1024 * 1024)
            if disk:
                snapshot.disk_read_bytes = disk.read_bytes
                snapshot.disk_write_bytes = disk.write_bytes
            if net:
                snapshot.network_recv_bytes = net.bytes_recv
                snapshot.network_sent_bytes = net.bytes_sent
        except ImportError:
            pass
        return snapshot

    def generate_report(self) -> PerformanceReport:
        """Generate aggregated performance report."""
        if not self._phases:
            return PerformanceReport()

        total_duration = sum(p.duration for p in self._phases)
        peak_cpu = max(p.cpu_percent for p in self._phases)
        avg_cpu = sum(p.cpu_percent for p in self._phases) / len(self._phases)
        peak_memory = max(p.memory_mb for p in self._phases)
        avg_memory = sum(p.memory_mb for p in self._phases) / len(self._phases)
        total_io = sum(p.io_operations for p in self._phases)
        total_net = sum(p.network_calls for p in self._phases)

        slowest = max(self._phases, key=lambda p: p.duration)
        bottleneck = self._identify_bottleneck()

        report = PerformanceReport(
            total_duration=total_duration,
            peak_cpu=peak_cpu,
            avg_cpu=avg_cpu,
            peak_memory_mb=peak_memory,
            avg_memory_mb=avg_memory,
            total_io_operations=total_io,
            total_network_calls=total_net,
            phases=list(self._phases),
            bottleneck_phase=bottleneck,
            slowest_phase=slowest.phase,
        )

        self._reports.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "report": report.to_dict(),
        })
        self._save()

        return report

    def _identify_bottleneck(self) -> str:
        """Identify the bottleneck phase based on duration and resource usage."""
        if not self._phases:
            return ""

        scored = []
        for phase in self._phases:
            score = phase.duration * 0.5
            score += phase.cpu_percent * 0.2
            score += phase.memory_mb * 0.001
            score += phase.io_operations * 0.0001
            scored.append((score, phase.phase))

        scored.sort(reverse=True)
        return scored[0][1] if scored else ""

    def get_phase_duration(self, phase: str) -> float:
        """Get duration for a specific phase."""
        for p in self._phases:
            if p.phase == phase:
                return p.duration
        return 0.0

    def format_report(self, report: Optional[PerformanceReport] = None) -> str:
        """Format a human-readable performance report."""
        report = report or self.generate_report()
        lines = [
            "Performance Report",
            "=" * 50,
            f"  Total Duration:     {report.total_duration:.2f}s",
            f"  Peak CPU:           {report.peak_cpu:.1f}%",
            f"  Avg CPU:            {report.avg_cpu:.1f}%",
            f"  Peak Memory:        {report.peak_memory_mb:.1f} MB",
            f"  Avg Memory:         {report.avg_memory_mb:.1f} MB",
            f"  I/O Operations:     {report.total_io_operations:,}",
            f"  Network Calls:      {report.total_network_calls:,}",
            f"  Slowest Phase:      {report.slowest_phase}",
            f"  Bottleneck:         {report.bottleneck_phase}",
            "",
            "Phase Breakdown:",
            "-" * 50,
        ]
        for phase in report.phases:
            lines.append(f"  {phase.phase:<20} {phase.duration:>8.2f}s  CPU:{phase.cpu_percent:>5.1f}%  MEM:{phase.memory_mb:>8.1f}MB")
        return "\n".join(lines)


class _PhaseTimer:
    """Context manager for timing a phase."""

    def __init__(self, tracker: PerformanceTracker, phase: str):
        self.tracker = tracker
        self.phase = phase

    def __enter__(self):
        self.tracker.start_phase(self.phase)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tracker.end_phase(self.phase)
        return False
