from datetime import datetime, timezone

from app.benchmark.benchmark_history import BenchmarkHistory
from app.benchmark.golden_suite import GoldenBenchmarkSuite
from app.benchmark.release_quality_gate import ReleaseQualityGate
from app.brain.brain_pipeline import BrainPipeline


class GoldenBenchmarkRunner:
    """Runs deterministic, non-destructive engineering preflight benchmarks.

    Full project creation is deliberately left to an injected execution handler,
    so a benchmark cannot unexpectedly create twenty projects or make LLM calls.
    """

    def __init__(self, suite=None, pipeline_factory=None, history=None, quality_gate=None):
        self.suite = suite or GoldenBenchmarkSuite()
        self.pipeline_factory = pipeline_factory or BrainPipeline
        self.history = history or BenchmarkHistory()
        self.quality_gate = quality_gate or ReleaseQualityGate(required_projects=len(self.suite.projects()))

    def run(self, tier=None, execute=False, execution_handler=None):
        if execute and not callable(execution_handler):
            raise ValueError("An execution_handler is required for destructive benchmark execution")
        results = [self._run_project(project, execute, execution_handler) for project in self.suite.projects(tier)]
        total = len(results)
        preflight_passed = sum(item["preflight_passed"] for item in results)
        ready = sum(item["status"] == "ready" for item in results)
        report = {
            "kind": "golden_benchmark",
            "mode": "execution" if execute else "preflight",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total": total,
            "preflight_passed": preflight_passed,
            "ready": ready,
            "approval_required": sum(item["status"] == "needs_approval" for item in results),
            "preflight_rate": round(preflight_passed / total, 4) if total else 0.0,
            "ready_rate": round(ready / total, 4) if total else 0.0,
            "tiers": self._tier_summary(results),
            "results": results,
        }
        report["quality_gate"] = self.quality_gate.evaluate(report)
        self.history.record(report)
        return report

    def _run_project(self, project, execute, execution_handler):
        brief = self.pipeline_factory().prepare(project.goal)
        requirements = brief["requirements"]
        architecture = brief["architecture"]
        simulation = brief["simulation"]
        missing_features = sorted(set(project.required_features) - set(requirements.get("features", ())))
        checks = {
            "requirements_valid": bool(requirements.get("valid")),
            "required_features_detected": not missing_features,
            "architecture_valid": bool(architecture.get("valid")),
            "strategy_selected": bool(brief.get("strategy", {}).get("selected")),
            "simulation_complete": simulation.get("estimated_files", 0) > 0 and simulation.get("estimated_minutes", 0) > 0,
            "optimized_verification": any("validate" in step.get("name", "") and "test" in step.get("name", "") for step in brief.get("execution", {}).get("steps", ())),
        }
        preflight_passed = all(checks.values())
        approval = brief["approval"]
        if not preflight_passed:
            status = "failed"
        elif approval["approved"]:
            status = "ready"
        else:
            status = "needs_approval"
        result = {
            "project": project.to_dict(),
            "status": status,
            "preflight_passed": preflight_passed,
            "checks": checks,
            "missing_features": missing_features,
            "risk": brief["risk"],
            "approval": approval,
            "strategy": brief["strategy"]["selected"],
            "simulation": simulation,
        }
        if execute and status == "ready":
            execution = execution_handler(project, brief)
            result["execution"] = execution
            if not bool(execution.get("success")):
                result["status"] = "execution_failed"
        return result

    @staticmethod
    def _tier_summary(results):
        summary = {}
        for result in results:
            tier = result["project"]["tier"]
            bucket = summary.setdefault(tier, {"total": 0, "preflight_passed": 0, "ready": 0})
            bucket["total"] += 1
            bucket["preflight_passed"] += int(result["preflight_passed"])
            bucket["ready"] += int(result["status"] == "ready")
        return summary
