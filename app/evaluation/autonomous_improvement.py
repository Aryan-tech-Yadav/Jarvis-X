"""Safe, benchmark-gated autonomous improvement orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional

from app.self_improvement.benchmark import BenchmarkEngine
from app.self_improvement.comparator import BenchmarkComparator
from app.self_improvement.sandbox import SandboxBuilder
from app.self_improvement.version_manager import VersionManager


@dataclass(frozen=True)
class ImprovementDecision:
    """Decision and evidence for one candidate improvement."""

    opportunity_id: str
    accepted: bool
    reason: str
    comparison: Dict[str, Any]
    sandbox_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "opportunity_id": self.opportunity_id,
            "accepted": self.accepted,
            "reason": self.reason,
            "comparison": dict(self.comparison),
            "sandbox_id": self.sandbox_id,
        }


class AutonomousImprovementEngine:
    """Evaluate isolated candidates and adopt only measurable improvements."""

    def __init__(
        self,
        project_path: str,
        *,
        sandbox_builder: Optional[SandboxBuilder] = None,
        benchmark_engine: Optional[BenchmarkEngine] = None,
        comparator: Optional[BenchmarkComparator] = None,
        version_manager: Optional[VersionManager] = None,
    ):
        self.project_path = project_path
        self.sandboxes = sandbox_builder or SandboxBuilder()
        self.benchmark = benchmark_engine or BenchmarkEngine(project_path)
        self.comparator = comparator or BenchmarkComparator()
        self.versions = version_manager or VersionManager()
        self._rollback_versions: Dict[str, str] = {}

    def improve(
        self,
        opportunities: Iterable[Dict[str, Any]],
        candidate_builder: Callable[[Dict[str, Any], str], bool],
    ) -> Dict[str, Any]:
        """Run candidate improvements in sandboxes and return auditable decisions.

        ``candidate_builder`` receives an opportunity and sandbox path. It must
        write the candidate into that sandbox and return whether it changed it.
        """
        if not callable(candidate_builder):
            raise TypeError("candidate_builder must be callable")

        baseline = self.benchmark.run_benchmark(self.project_path, version="baseline")
        decisions: List[ImprovementDecision] = []
        for opportunity in opportunities:
            opportunity_id = str(opportunity.get("id", "")).strip()
            if not opportunity_id:
                raise ValueError("Every improvement opportunity requires an id")

            sandbox = self.sandboxes.create(self.project_path, opportunity_id)
            changed = candidate_builder(opportunity, sandbox.sandbox_path)
            if not changed:
                self.sandboxes.discard(sandbox.sandbox_id)
                decisions.append(ImprovementDecision(
                    opportunity_id, False, "Candidate produced no change", {}, sandbox.sandbox_id
                ))
                continue

            candidate = self.benchmark.run_benchmark(
                sandbox.sandbox_path, version=f"candidate-{opportunity_id}"
            )
            comparison = self.comparator.compare(baseline.to_dict(), candidate.to_dict())
            accepted = comparison.get("overall_change", 0.0) > 0 and not comparison.get("regressions")
            if accepted:
                snapshot = self.versions.create_version(
                    self.project_path, version_name=f"before-{opportunity_id}",
                    score=baseline.quality_score,
                )
                if not self.sandboxes.promote(sandbox.sandbox_id, self.project_path):
                    self.versions.activate(snapshot.version_id)
                    accepted = False
                    reason = "Promotion failed; baseline restored"
                else:
                    self._rollback_versions[opportunity_id] = snapshot.version_id
                    reason = "Candidate benchmark improved without regressions"
            else:
                self.sandboxes.discard(sandbox.sandbox_id)
                reason = "Candidate rejected by benchmark gate"

            decisions.append(ImprovementDecision(
                opportunity_id, accepted, reason, comparison, sandbox.sandbox_id
            ))
            if accepted:
                baseline = candidate

        return {
            "kind": "autonomous_improvement",
            "baseline": baseline.to_dict(),
            "accepted": sum(decision.accepted for decision in decisions),
            "rejected": sum(not decision.accepted for decision in decisions),
            "decisions": [decision.to_dict() for decision in decisions],
        }

    def rollback(self, opportunity_id: str) -> bool:
        """Restore the baseline snapshot saved for an accepted improvement."""
        version_id = self._rollback_versions.get(opportunity_id)
        if not version_id:
            raise ValueError(f"No rollback snapshot found for: {opportunity_id}")
        restored = self.versions.activate(version_id)
        if restored:
            del self._rollback_versions[opportunity_id]
        return restored
