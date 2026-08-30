"""Engineering benchmark facade.

Wraps the existing QA engines so the engineering pipeline can score
a generated project with a stable benchmark contract.
"""

from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.quality.qa_engine import QAEngine
from app.quality.quality_score import QualityScoreEngine


class Benchmark:
    """Evaluate a generated project against quality, security, and performance gates."""

    def __init__(self, qa_engine=None, score_engine=None):
        self.qa_engine = qa_engine or QAEngine()
        self.score_engine = score_engine or QualityScoreEngine()

    def evaluate(self, project_path: str) -> ExecutionResult:
        if not isinstance(project_path, str) or not project_path.strip():
            return ExecutionResult.failed("Project path cannot be empty")

        try:
            quality_score, static_result = self.qa_engine.evaluate_quality(project_path)
            return ExecutionResult.completed(
                data={
                    "overall_score": quality_score.overall_score,
                    "grade": quality_score.grade,
                    "passed_gate": quality_score.passed_gate,
                    "gate_reasons": quality_score.gate_reasons,
                    "suggestions": quality_score.suggestions,
                    "category_scores": {
                        name: {
                            "score": cs.score,
                            "weight": cs.weight,
                        }
                        for name, cs in quality_score.category_scores.items()
                    },
                    "static_analysis": {
                        "complexity_score": static_result.complexity_score,
                        "complexity_level": static_result.complexity_level,
                        "dead_functions": len(static_result.dead_functions),
                        "dead_files": len(static_result.dead_files),
                        "duplicate_blocks": len(static_result.duplicate_blocks),
                        "circular_imports": len(static_result.circular_imports),
                        "issues_count": len(static_result.issues),
                    },
                },
                message="Benchmark evaluation complete",
                metrics={"overall_score": quality_score.overall_score, "grade": quality_score.grade},
            )
        except Exception as exc:
            Logger.error(f"Benchmark evaluation failed: {exc}")
            return ExecutionResult.failed(str(exc))
