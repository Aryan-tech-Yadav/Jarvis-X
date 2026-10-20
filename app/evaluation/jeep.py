"""Evidence-driven evaluation and evolution facade for Jarvis-X."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from app.benchmark.reliability import ReliabilityLedger, ReliabilityRun
from app.evolution.self_evolution_engine import SelfEvolutionEngine
from app.quality.comprehensive_scorer import ComprehensiveQualityScorer
from app.quality.root_cause_engine import RootCauseEngine


@dataclass(frozen=True)
class EvaluationRecord:
    """A comparable, persisted evaluation of one project release."""

    project_name: str
    version: str
    evaluated_at: str
    quality: Dict[str, Any]
    failures: List[Dict[str, Any]]
    reliability: Dict[str, Any]
    evolution: Dict[str, Any]
    wisdom: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EngineeringEvaluationPlatform:
    """Coordinate project scoring, failure diagnosis, reliability, and learning."""

    def __init__(
        self,
        *,
        reliability_ledger: Optional[ReliabilityLedger] = None,
        evolution_engine: Optional[SelfEvolutionEngine] = None,
        root_cause_engine: Optional[RootCauseEngine] = None,
    ):
        self.reliability = reliability_ledger or ReliabilityLedger()
        self.evolution = evolution_engine or SelfEvolutionEngine()
        self.root_cause = root_cause_engine or RootCauseEngine()
        self._records: List[EvaluationRecord] = []

    def evaluate_project(
        self,
        project_name: str,
        project_path: str,
        *,
        version: str = "current",
        failures: Optional[Iterable[Dict[str, Any]]] = None,
        lessons: Optional[List[str]] = None,
        agent: str = "engineering",
        wisdom_answers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Evaluate a release using observable project and failure evidence."""
        if not project_name or not project_name.strip():
            raise ValueError("Project name cannot be empty")
        if not version or not version.strip():
            raise ValueError("Version cannot be empty")

        quality = ComprehensiveQualityScorer(project_path).score()
        failure_reports = self._diagnose_failures(failures or [])
        success = quality.passed_gate and not failure_reports
        reliability = self.reliability.record(
            ReliabilityRun(
                benchmark_id=f"{project_name.strip()}:{version.strip()}",
                success=success,
                error=failure_reports[0]["failure"] if failure_reports else None,
            )
        )
        evolution = self.evolution.process_project(
            project_name.strip(),
            result="SUCCESS" if success else "FAILED",
            quality_score=quality.overall_score,
            test_coverage=quality.test_score,
            agent=agent,
            failures=[
                {
                    "category": report["error_category"],
                    "reason": report["root_cause"],
                    "fix_strategy": report["repair_strategy"],
                }
                for report in failure_reports
            ],
            lessons=lessons,
        )
        wisdom = self._derive_wisdom(
            quality=self._quality_dict(quality),
            failures=failure_reports,
            lessons=lessons or [],
            answers=wisdom_answers,
        )
        record = EvaluationRecord(
            project_name=project_name.strip(),
            version=version.strip(),
            evaluated_at=datetime.now(timezone.utc).isoformat(),
            quality=self._quality_dict(quality),
            failures=failure_reports,
            reliability=reliability,
            evolution=evolution,
            wisdom=wisdom,
        )
        self._records.append(record)
        return record.to_dict()

    def compare_versions(self, current: str, baseline: str) -> Dict[str, Any]:
        """Compare two evaluated versions and report measurable regressions."""
        current_record = self._find_version(current)
        baseline_record = self._find_version(baseline)
        current_quality = current_record.quality
        baseline_quality = baseline_record.quality
        metrics = ("overall_score", "compile_score", "runtime_score", "test_score")
        deltas = {
            metric: round(float(current_quality[metric]) - float(baseline_quality[metric]), 2)
            for metric in metrics
        }
        regressions = [metric for metric, delta in deltas.items() if delta < 0]
        return {
            "kind": "version_comparison",
            "current": current,
            "baseline": baseline,
            "deltas": deltas,
            "regressions": regressions,
            "better": not regressions and deltas["overall_score"] >= 0,
        }

    def records(self) -> List[Dict[str, Any]]:
        """Return all release evaluations in chronological order."""
        return [record.to_dict() for record in self._records]

    def wisdom(self) -> List[Dict[str, Any]]:
        """Return the five-question engineering reflection for each release."""
        return [record.wisdom for record in self._records]

    def _diagnose_failures(self, failures: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        reports = []
        for failure in failures:
            message = str(failure.get("message") or failure.get("error") or "Unknown failure")
            report = self.root_cause.diagnose(
                message,
                raw_traceback=str(failure.get("traceback", "")),
                context_code=failure.get("context_code"),
            )
            reports.append({
                "failure": report.failure,
                "root_cause": report.root_cause,
                "confidence": report.confidence,
                "repair_strategy": report.repair_strategy,
                "error_category": report.error_category,
                "target_files": list(report.target_files),
            })
        return reports

    @staticmethod
    def _quality_dict(quality: Any) -> Dict[str, Any]:
        return {
            "overall_score": quality.overall_score,
            "compile_score": quality.compile_score,
            "runtime_score": quality.runtime_score,
            "test_score": quality.test_score,
            "code_quality_score": quality.code_quality_score,
            "architecture_score": quality.architecture_score,
            "grade": quality.grade,
            "passed_gate": quality.passed_gate,
        }

    def _find_version(self, version: str) -> EvaluationRecord:
        for record in reversed(self._records):
            if record.version == version:
                return record
        raise ValueError(f"No evaluation found for version: {version}")

    @staticmethod
    def _derive_wisdom(
        *,
        quality: Dict[str, Any],
        failures: List[Dict[str, Any]],
        lessons: List[str],
        answers: Optional[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Create evidence-backed wisdom; caller answers override generated prompts."""
        first_failure = failures[0] if failures else None
        generated = {
            "best_decision": (
                f"Passed the quality gate with {quality['overall_score']:.2f}% overall quality."
                if quality["passed_gate"]
                else "No best decision recorded because the release did not pass the quality gate."
            ),
            "costliest_mistake": (
                first_failure["root_cause"] if first_failure
                else "No failure evidence was recorded for this release."
            ),
            "what_to_change": (
                first_failure["repair_strategy"] if first_failure
                else "Keep the current approach and validate it against the next benchmark."
            ),
            "reusable_principle": (
                lessons[0] if lessons
                else "Benchmark every release before treating an engineering change as an improvement."
            ),
            "philosophy_change": (
                "Increase confidence in the current engineering principles."
                if quality["passed_gate"] and not failures
                else "Strengthen prevention for the diagnosed failure before the next release."
            ),
        }
        if answers:
            for key in generated:
                value = answers.get(key)
                if value is not None and value.strip():
                    generated[key] = value.strip()
        return {
            "questions": generated,
            "evidence": {
                "quality_score": quality["overall_score"],
                "passed_gate": quality["passed_gate"],
                "failure_count": len(failures),
                "lessons_count": len(lessons),
            },
        }
