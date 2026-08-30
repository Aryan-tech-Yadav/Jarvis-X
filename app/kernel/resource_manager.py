"""Resource-pressure policy for the autonomous execution kernel.

The kernel deliberately separates observing resources from deciding whether a
new unit of work may be admitted.  Keeping the sampler injectable makes this
module deterministic in tests and lets a deployment supply platform-specific
CPU, memory, disk, or token measurements without changing scheduling policy.
"""

from __future__ import annotations

import os
import shutil
import tracemalloc
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Optional


def _validate_limit(name: str, value: Optional[int]) -> Optional[int]:
    """Validate an optional non-negative integral resource limit."""

    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer or None")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _default_sample() -> dict[str, int]:
    """Collect a small, portable default sample without optional packages."""

    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    disk = shutil.disk_usage(os.curdir)
    return {
        "process_memory_bytes": current,
        "process_peak_memory_bytes": peak,
        "disk_free_bytes": disk.free,
        "disk_total_bytes": disk.total,
    }


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    """Optional ceilings used by :class:`ResourceManager`.

    ``None`` disables an individual check.  An open-task limit is exceeded only
    when the count is greater than the configured limit, so a limit of ``2``
    permits exactly two open tasks.
    """

    max_memory_bytes: Optional[int] = None
    min_disk_free_bytes: Optional[int] = None
    max_open_tasks: Optional[int] = None

    def __post_init__(self) -> None:
        for name in ("max_memory_bytes", "min_disk_free_bytes", "max_open_tasks"):
            _validate_limit(name, getattr(self, name))

    def to_dict(self) -> dict[str, Optional[int]]:
        return {
            "max_memory_bytes": self.max_memory_bytes,
            "min_disk_free_bytes": self.min_disk_free_bytes,
            "max_open_tasks": self.max_open_tasks,
        }


@dataclass(frozen=True, slots=True)
class ResourceViolation:
    """One breached resource limit with machine- and human-readable detail."""

    code: str
    metric: str
    observed: int | float
    limit: int
    message: str

    @property
    def value(self) -> int | float:
        """Alias for ``observed`` for simple dashboard consumers."""

        return self.observed

    @property
    def threshold(self) -> int:
        """Alias for ``limit`` for generic alert renderers."""

        return self.limit

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "metric": self.metric,
            "observed": self.observed,
            "limit": self.limit,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ResourceReport:
    """The normalized resource sample and all limit violations in it."""

    sample: Mapping[str, Any]
    open_tasks: int
    limits: ResourceLimits
    violations: tuple[ResourceViolation, ...]

    @property
    def healthy(self) -> bool:
        return not self.violations

    @property
    def under_pressure(self) -> bool:
        return bool(self.violations)

    @property
    def status(self) -> str:
        return "healthy" if self.healthy else "pressure"

    def to_dict(self) -> dict[str, Any]:
        return {
            "healthy": self.healthy,
            "under_pressure": self.under_pressure,
            "status": self.status,
            "sample": dict(self.sample),
            "open_tasks": self.open_tasks,
            "limits": self.limits.to_dict(),
            "violations": [violation.to_dict() for violation in self.violations],
        }


@dataclass(frozen=True, slots=True)
class SchedulingDecision(Mapping[str, Any]):
    """A mapping-friendly decision returned before a job is scheduled."""

    allowed: bool
    action: str
    priority: int
    protected: bool
    report: ResourceReport
    warnings: tuple[str, ...] = ()

    @property
    def paused(self) -> bool:
        return self.action == "pause"

    @property
    def rejected(self) -> bool:
        return self.action == "reject"

    @property
    def violations(self) -> tuple[ResourceViolation, ...]:
        return self.report.violations

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe policy result for schedulers and dashboards."""

        return {
            "allowed": self.allowed,
            "action": self.action,
            "paused": self.paused,
            "rejected": self.rejected,
            "priority": self.priority,
            "protected": self.protected,
            "warnings": list(self.warnings),
            "violations": [violation.to_dict() for violation in self.violations],
            "resources": self.report.to_dict(),
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_dict()[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.to_dict())

    def __len__(self) -> int:
        return len(self.to_dict())

    def __bool__(self) -> bool:
        return self.allowed


class ResourceManager:
    """Evaluate resource limits and guard scheduling under pressure.

    ``sampler`` may be a zero-argument callable or an object exposing a
    zero-argument ``sample()`` method.  Its mapping may use either the kernel
    keys (``memory_bytes``, ``disk_free_bytes``, ``open_tasks``) or the legacy
    runtime key ``process_memory_bytes``.  Values not relevant to this policy
    are preserved in reports for downstream observability.

    During pressure, low-priority jobs are paused, ordinary higher-priority
    jobs are rejected, and only jobs *explicitly* marked protected and meeting
    ``protected_priority`` are allowed through.  Such bypasses always include a
    warning and remain visible in the returned decision.
    """

    _MEMORY_KEYS = ("memory_bytes", "process_memory_bytes", "ram_bytes", "memory_usage_bytes")
    _DISK_KEYS = ("disk_free_bytes", "free_disk_bytes", "disk_free")
    _TASK_KEYS = ("open_tasks", "active_tasks", "running_tasks", "task_count")

    def __init__(
        self,
        sampler: Callable[[], Mapping[str, Any]] | Any | None = None,
        max_memory_bytes: Optional[int] = None,
        min_disk_free_bytes: Optional[int] = None,
        max_open_tasks: Optional[int] = None,
        *,
        low_priority_threshold: int = 0,
        protected_priority: int = 1,
    ) -> None:
        if isinstance(low_priority_threshold, bool) or not isinstance(low_priority_threshold, int):
            raise TypeError("low_priority_threshold must be an integer")
        if isinstance(protected_priority, bool) or not isinstance(protected_priority, int):
            raise TypeError("protected_priority must be an integer")
        if protected_priority <= low_priority_threshold:
            raise ValueError("protected_priority must be greater than low_priority_threshold")

        self._sampler = self._coerce_sampler(sampler)
        self.limits = ResourceLimits(max_memory_bytes, min_disk_free_bytes, max_open_tasks)
        self.low_priority_threshold = low_priority_threshold
        self.protected_priority = protected_priority
        self._open_tasks = 0
        self._open_task_ids: set[str] = set()
        self._last_report: ResourceReport | None = None

    @property
    def open_tasks(self) -> int:
        """The locally tracked count used when no count is supplied by a sampler."""

        return self._open_tasks

    @property
    def last_report(self) -> ResourceReport | None:
        return self._last_report

    def sample(self) -> dict[str, Any]:
        """Return a normalized copy of the current resource sample."""

        raw = self._sampler()
        if not isinstance(raw, Mapping):
            raise TypeError("Resource sampler must return a mapping")
        return self._normalize_sample(raw)

    def set_open_tasks(self, count: int) -> int:
        """Set a caller-managed open-task count and return it."""

        self._open_tasks = self._validate_task_count(count)
        self._open_task_ids.clear()
        return self._open_tasks

    def task_opened(self, task_id: str) -> int:
        """Record a task becoming open; duplicate ids do not inflate the count."""

        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")
        self._open_task_ids.add(task_id)
        self._open_tasks = len(self._open_task_ids)
        return self._open_tasks

    def task_closed(self, task_id: str) -> bool:
        """Record a task completing, failing, or being cancelled."""

        existed = task_id in self._open_task_ids
        self._open_task_ids.discard(task_id)
        self._open_tasks = len(self._open_task_ids)
        return existed

    # Natural aliases for schedulers with acquire/release terminology.
    open_task = task_opened
    close_task = task_closed

    def assess(
        self,
        sample: Mapping[str, Any] | None = None,
        open_tasks: int | None = None,
    ) -> ResourceReport:
        """Assess a sample against limits without admitting or mutating a job."""

        normalized = self.sample() if sample is None else self._normalize_mapping(sample)
        task_count = self._task_count(normalized, open_tasks)
        normalized["open_tasks"] = task_count

        violations: list[ResourceViolation] = []
        memory = self._metric(normalized, self._MEMORY_KEYS)
        if self.limits.max_memory_bytes is not None and memory is not None and memory > self.limits.max_memory_bytes:
            violations.append(
                ResourceViolation(
                    "memory_limit_exceeded",
                    "memory_bytes",
                    memory,
                    self.limits.max_memory_bytes,
                    f"Memory usage {memory} exceeds limit {self.limits.max_memory_bytes}",
                )
            )

        disk_free = self._metric(normalized, self._DISK_KEYS)
        if (
            self.limits.min_disk_free_bytes is not None
            and disk_free is not None
            and disk_free < self.limits.min_disk_free_bytes
        ):
            violations.append(
                ResourceViolation(
                    "disk_free_below_minimum",
                    "disk_free_bytes",
                    disk_free,
                    self.limits.min_disk_free_bytes,
                    f"Disk free space {disk_free} is below minimum {self.limits.min_disk_free_bytes}",
                )
            )

        if self.limits.max_open_tasks is not None and task_count > self.limits.max_open_tasks:
            violations.append(
                ResourceViolation(
                    "open_tasks_limit_exceeded",
                    "open_tasks",
                    task_count,
                    self.limits.max_open_tasks,
                    f"Open task count {task_count} exceeds limit {self.limits.max_open_tasks}",
                )
            )

        report = ResourceReport(dict(normalized), task_count, self.limits, tuple(violations))
        self._last_report = report
        return report

    # Readable aliases for dashboards and health checks.
    report = assess
    check = assess

    def violations(
        self,
        sample: Mapping[str, Any] | None = None,
        open_tasks: int | None = None,
    ) -> list[ResourceViolation]:
        """Return only the current limit violations."""

        return list(self.assess(sample, open_tasks).violations)

    def is_under_pressure(
        self,
        sample: Mapping[str, Any] | None = None,
        open_tasks: int | None = None,
    ) -> bool:
        return self.assess(sample, open_tasks).under_pressure

    def scheduling_decision(
        self,
        priority: int = 0,
        open_tasks: int | None = None,
        *,
        protected: bool = False,
        sample: Mapping[str, Any] | None = None,
    ) -> SchedulingDecision:
        """Return a mapping-compatible admission decision for a pending job.

        This intentionally does not reserve a task slot.  A scheduler should
        call :meth:`task_opened` only after it has actually accepted work, so a
        rejected or paused job cannot leak open-task capacity.
        """

        if isinstance(priority, bool) or not isinstance(priority, int):
            raise TypeError("priority must be an integer")
        report = self.assess(sample, open_tasks)
        protected = bool(protected)
        if report.healthy:
            return SchedulingDecision(True, "allow", priority, protected, report)

        violation_names = ", ".join(violation.code for violation in report.violations)
        if protected and priority >= self.protected_priority:
            warning = (
                "Protected high-priority job admitted under resource pressure: "
                f"{violation_names}"
            )
            return SchedulingDecision(True, "allow", priority, True, report, (warning,))

        if priority <= self.low_priority_threshold:
            warning = f"Low-priority job paused under resource pressure: {violation_names}"
            return SchedulingDecision(False, "pause", priority, protected, report, (warning,))

        warning = f"Job rejected under resource pressure: {violation_names}"
        if protected:
            warning = (
                f"Protected job priority {priority} is below protected priority "
                f"{self.protected_priority}; {warning}"
            )
        return SchedulingDecision(False, "reject", priority, protected, report, (warning,))

    # Small aliases make adoption straightforward in dispatchers.
    admit = scheduling_decision
    decide = scheduling_decision

    def can_schedule(self, priority: int = 0, open_tasks: int | None = None, **kwargs: Any) -> bool:
        """Return just the admission boolean for minimal schedulers."""

        return self.scheduling_decision(priority, open_tasks, **kwargs).allowed

    def should_pause(self, priority: int = 0, open_tasks: int | None = None, **kwargs: Any) -> bool:
        """Whether a low-priority job should remain queued under pressure."""

        return self.scheduling_decision(priority, open_tasks, **kwargs).paused

    @staticmethod
    def _coerce_sampler(sampler: Callable[[], Mapping[str, Any]] | Any | None) -> Callable[[], Mapping[str, Any]]:
        if sampler is None:
            return _default_sample
        candidate = getattr(sampler, "sample", sampler)
        if not callable(candidate):
            raise TypeError("sampler must be callable or expose a callable sample() method")
        return candidate

    def _normalize_mapping(self, sample: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(sample, Mapping):
            raise TypeError("sample must be a mapping")
        return self._normalize_sample(sample)

    def _normalize_sample(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        sample = dict(raw)
        memory = self._metric(sample, self._MEMORY_KEYS)
        disk_free = self._metric(sample, self._DISK_KEYS)
        task_count = self._metric(sample, self._TASK_KEYS)
        if memory is not None:
            sample.setdefault("memory_bytes", memory)
        if disk_free is not None:
            sample.setdefault("disk_free_bytes", disk_free)
        if task_count is not None:
            sample.setdefault("open_tasks", self._validate_task_count(task_count))
        return sample

    def _task_count(self, sample: Mapping[str, Any], explicit_count: int | None) -> int:
        if explicit_count is not None:
            return self._validate_task_count(explicit_count)
        sampled_count = self._metric(sample, self._TASK_KEYS)
        if sampled_count is not None:
            return self._validate_task_count(sampled_count)
        return self._open_tasks

    @staticmethod
    def _validate_task_count(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
            raise TypeError("open_tasks must be a non-negative integer")
        count = int(value)
        if count < 0:
            raise ValueError("open_tasks must be non-negative")
        return count

    @staticmethod
    def _metric(sample: Mapping[str, Any], keys: tuple[str, ...]) -> int | float | None:
        for key in keys:
            if key not in sample or sample[key] is None:
                continue
            value = sample[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"Resource metric {key} must be numeric")
            if value < 0:
                raise ValueError(f"Resource metric {key} must be non-negative")
            return value
        return None


__all__ = [
    "ResourceLimits",
    "ResourceManager",
    "ResourceReport",
    "ResourceViolation",
    "SchedulingDecision",
]
