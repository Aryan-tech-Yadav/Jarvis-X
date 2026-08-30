"""Evolution Engine - Controlled system improvement.

Week 6: Evolution Engine
Har 50 tasks ke baad:
  Collect Metrics -> Find Weakest Area -> Generate Improvement Proposal -> Benchmark -> Accept/Reject

Ye controlled evolution hogi.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logger import Logger


@dataclass
class ImprovementProposal:
    """Proposal for system improvement."""
    proposal_id: str
    target_module: str
    description: str
    expected_impact: float = 0.0
    implementation_cost: float = 0.0
    priority: str = "medium"  # low, medium, high, critical
    status: str = "proposed"  # proposed, accepted, rejected, implemented
    created_at: str = ""
    benchmark_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvolutionReport:
    """Evolution cycle report."""
    cycle_id: str
    timestamp: str
    tasks_analyzed: int
    weakest_area: str
    proposals_generated: int
    proposals_accepted: int
    proposals_rejected: int
    overall_improvement: float = 0.0
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "cycle_id": self.cycle_id,
            "timestamp": self.timestamp,
            "tasks_analyzed": self.tasks_analyzed,
            "weakest_area": self.weakest_area,
            "proposals_generated": self.proposals_generated,
            "proposals_accepted": self.proposals_accepted,
            "proposals_rejected": self.proposals_rejected,
            "overall_improvement": self.overall_improvement,
            "details": self.details,
        }


class EvolutionEngine:
    """Controlled evolution based on task metrics.

    Every N tasks:
      1. Collect metrics
      2. Find weakest area
      3. Generate improvement proposal
      4. Benchmark
      5. Accept/Reject
    """

    def __init__(self, evolution_cycle: int = 50, event_bus=None, ai_router=None):
        self.evolution_cycle = evolution_cycle
        self.event_bus = event_bus
        self.ai_router = ai_router
        self._proposals: List[ImprovementProposal] = []
        self._evolution_history: List[EvolutionReport] = []
        self._task_counter = 0
        self._metrics_history: List[Dict[str, Any]] = []

    def record_task(self, task_result: Dict[str, Any]):
        """Record task result for evolution analysis.

        Args:
            task_result: Task execution result
        """
        self._task_counter += 1
        self._metrics_history.append(task_result)

        if self._task_counter % self.evolution_cycle == 0:
            self._run_evolution_cycle()

    def _run_evolution_cycle(self) -> EvolutionReport:
        """Run evolution cycle."""
        start_time = time.perf_counter()
        cycle_id = f"evo_{int(time.time())}"

        Logger.info(f"[Evolution] Running cycle {cycle_id} after {self._task_counter} tasks")

        # Step 1: Collect metrics
        metrics = self._collect_metrics()
        self._emit("EVOLUTION_METRICS_COLLECTED", {"cycle_id": cycle_id, "metrics": metrics})

        # Step 2: Find weakest area
        weakest_area = self._find_weakest_area(metrics)
        self._emit("EVOLUTION_WEAKEST_AREA", {"cycle_id": cycle_id, "area": weakest_area})

        # Step 3: Generate proposals
        proposals = self._generate_proposals(weakest_area, metrics)
        self._emit("EVOLUTION_PROPOSALS_GENERATED", {"cycle_id": cycle_id, "count": len(proposals)})

        # Step 4: Benchmark proposals
        accepted, rejected = self._benchmark_proposals(proposals)
        self._emit("EVOLUTION_PROPOSALS_REVIEWED", {"cycle_id": cycle_id, "accepted": len(accepted), "rejected": len(rejected)})

        # Calculate improvement
        improvement = self._calculate_improvement(metrics)

        report = EvolutionReport(
            cycle_id=cycle_id,
            timestamp=datetime.now().isoformat(),
            tasks_analyzed=self.evolution_cycle,
            weakest_area=weakest_area,
            proposals_generated=len(proposals),
            proposals_accepted=len(accepted),
            proposals_rejected=len(rejected),
            overall_improvement=improvement,
            details=[f"Weakest area: {weakest_area}", f"Proposals: {len(accepted)} accepted, {len(rejected)} rejected"],
        )

        self._evolution_history.append(report)
        self._save_report(report)

        return report

    def _collect_metrics(self) -> Dict[str, Any]:
        """Collect metrics from last N tasks."""
        recent = self._metrics_history[-self.evolution_cycle:]
        if not recent:
            return {}

        metrics = {
            "total_tasks": len(recent),
            "success_rate": sum(1 for t in recent if t.get("success")) / len(recent),
            "average_quality": sum(t.get("quality_score", 0.0) for t in recent) / len(recent),
            "average_duration": sum(t.get("metrics", {}).get("duration_seconds", 0.0) for t in recent) / len(recent),
            "total_errors": sum(len(t.get("errors", [])) for t in recent),
            "total_repairs": sum(t.get("metrics", {}).get("errors_fixed", 0) for t in recent),
        }

        # Per-module metrics
        module_performance: Dict[str, List[float]] = {}
        for task in recent:
            module = task.get("module", "unknown")
            score = task.get("quality_score", 0.0)
            if module not in module_performance:
                module_performance[module] = []
            module_performance[module].append(score)

        metrics["module_performance"] = {
            module: sum(scores) / len(scores)
            for module, scores in module_performance.items()
        }

        return metrics

    def _find_weakest_area(self, metrics: Dict[str, Any]) -> str:
        """Find weakest area from metrics."""
        module_perf = metrics.get("module_performance", {})

        if not module_perf:
            return "general"

        # Find module with lowest average quality
        weakest = min(module_perf, key=module_perf.get)
        weakest_score = module_perf[weakest]

        if weakest_score < 70.0:
            return f"{weakest} (score: {weakest_score:.0f}%)"

        # Check other metrics
        if metrics.get("success_rate", 1.0) < 0.8:
            return "success_rate"
        if metrics.get("average_quality", 100.0) < 80.0:
            return "quality"
        if metrics.get("total_errors", 0) > 10:
            return "error_handling"

        return "general"

    def _generate_proposals(self, weakest_area: str, metrics: Dict[str, Any]) -> List[ImprovementProposal]:
        """Generate improvement proposals."""
        proposals = []

        # Generate proposals based on weakest area
        if "quality" in weakest_area or weakest_area == "general":
            proposals.append(ImprovementProposal(
                proposal_id=f"prop_{int(time.time())}_1",
                target_module="code_generation",
                description="Improve code generation quality through better prompting",
                expected_impact=15.0,
                implementation_cost=20.0,
                priority="high",
            ))

        if "error" in weakest_area:
            proposals.append(ImprovementProposal(
                proposal_id=f"prop_{int(time.time())}_2",
                target_module="error_handling",
                description="Add proactive error prevention checks",
                expected_impact=10.0,
                implementation_cost=15.0,
                priority="medium",
            ))

        if "success_rate" in weakest_area:
            proposals.append(ImprovementProposal(
                proposal_id=f"prop_{int(time.time())}_3",
                target_module="execution",
                description="Add retry mechanism with exponential backoff",
                expected_impact=20.0,
                implementation_cost=25.0,
                priority="high",
            ))

        # Use AI to generate proposals if available
        if self.ai_router and not proposals:
            try:
                prompt = f"""Generate improvement proposals for weakest area: {weakest_area}

Metrics: {json.dumps(metrics)[:500]}

Return JSON array:
[{{"target_module": "...", "description": "...", "expected_impact": 10, "priority": "high"}}]

JSON:"""
                response = self.ai_router.ask(prompt, task_type="evolution")
                json_match = self._extract_json(response)
                if json_match:
                    data = json.loads(json_match)
                    for item in data[:3]:
                        proposals.append(ImprovementProposal(
                            proposal_id=f"prop_{int(time.time())}_{len(proposals)+1}",
                            target_module=item.get("target_module", "general"),
                            description=item.get("description", ""),
                            expected_impact=item.get("expected_impact", 10.0),
                            implementation_cost=item.get("implementation_cost", 20.0),
                            priority=item.get("priority", "medium"),
                        ))
            except Exception:
                pass

        return proposals

    def _benchmark_proposals(self, proposals: List[ImprovementProposal]) -> tuple[List[ImprovementProposal], List[ImprovementProposal]]:
        """Benchmark and filter proposals."""
        accepted = []
        rejected = []

        for proposal in proposals:
            # Simple scoring: impact / cost ratio
            if proposal.implementation_cost > 0:
                ratio = proposal.expected_impact / proposal.implementation_cost
            else:
                ratio = proposal.expected_impact

            if ratio >= 0.5 and proposal.expected_impact >= 5.0:
                proposal.status = "accepted"
                accepted.append(proposal)
                self._proposals.append(proposal)
            else:
                proposal.status = "rejected"
                rejected.append(proposal)

        return accepted, rejected

    def _calculate_improvement(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall improvement."""
        if not self._metrics_history or len(self._metrics_history) < self.evolution_cycle * 2:
            return 0.0

        # Compare current cycle with previous
        current = self._metrics_history[-self.evolution_cycle:]
        previous = self._metrics_history[-self.evolution_cycle * 2:-self.evolution_cycle]

        current_avg = sum(t.get("quality_score", 0.0) for t in current) / len(current)
        previous_avg = sum(t.get("quality_score", 0.0) for t in previous) / len(previous)

        if previous_avg > 0:
            return ((current_avg - previous_avg) / previous_avg) * 100.0
        return 0.0

    def _extract_json(self, text: str) -> Optional[str]:
        """Extract JSON from text."""
        import re
        json_match = re.search(r"\[.*\]", text, re.DOTALL)
        if json_match:
            return json_match.group()
        return None

    def _save_report(self, report: EvolutionReport):
        """Save evolution report."""
        try:
            report_path = Path("data/evolution")
            report_path.mkdir(parents=True, exist_ok=True)
            filepath = report_path / f"evolution_{report.cycle_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({
                    "cycle_id": report.cycle_id,
                    "timestamp": report.timestamp,
                    "tasks_analyzed": report.tasks_analyzed,
                    "weakest_area": report.weakest_area,
                    "proposals_generated": report.proposals_generated,
                    "proposals_accepted": report.proposals_accepted,
                    "proposals_rejected": report.proposals_rejected,
                    "overall_improvement": report.overall_improvement,
                    "details": report.details,
                }, f, indent=2)
        except Exception as exc:
            Logger.warning(f"[Evolution] Save failed: {exc}")

    def _emit(self, event_type: str, payload: Dict[str, Any]):
        """Emit event through event bus."""
        if self.event_bus:
            try:
                self.event_bus.publish(event_type, payload)
            except Exception:
                pass

    def get_evolution_stats(self) -> Dict[str, Any]:
        """Get evolution statistics."""
        return {
            "total_cycles": len(self._evolution_history),
            "total_tasks": self._task_counter,
            "total_proposals": len(self._proposals),
            "accepted_proposals": sum(1 for p in self._proposals if p.status == "accepted"),
            "latest_report": self._evolution_history[-1].to_dict() if self._evolution_history else None,
        }
