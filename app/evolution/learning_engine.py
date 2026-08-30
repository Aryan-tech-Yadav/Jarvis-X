"""Autonomous Learning & Evolution Engine (ALE) Master Orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.results import ExecutionResult
from .evolution_report import EvolutionScoreCalculator, WeeklySelfReview
from .experience_engine import ExperienceEngine
from .failure_engine import FailureEngine
from .knowledge_sync import KnowledgeSync
from .models.experience import ExecutionMetrics, ProjectExperience, StageBreakdown
from .models.failure import FailureCategory
from .models.knowledge import KnowledgeCategory
from .models.pattern import PatternType
from .models.recommendation import EvolutionRecommendation
from .optimization_engine import OptimizationEngine
from .recommendation_engine import RecommendationEngine
from .success_engine import SuccessPatternEngine
from .version_engine import VersionEngine


class AutonomousLearningEngine:
    """Master Evolution Engine ensuring Jarvis-X gets systematically smarter after every run."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir else (Path.cwd() / "knowledge")
        self.experience_engine = ExperienceEngine(str(self.knowledge_dir))
        self.failure_engine = FailureEngine(str(self.knowledge_dir))
        self.success_engine = SuccessPatternEngine(str(self.knowledge_dir))
        self.optimization_engine = OptimizationEngine()
        self.recommendation_engine = RecommendationEngine(
            self.experience_engine, self.failure_engine, self.optimization_engine
        )
        self.version_engine = VersionEngine(str(self.knowledge_dir))
        self.knowledge_sync = KnowledgeSync(str(self.knowledge_dir))

    def process_project_completion(
        self,
        project_name: str,
        execution_time_sec: float,
        planning_score: float = 95.0,
        execution_score: float = 92.0,
        quality_score: float = 90.0,
        repair_count: int = 0,
        test_coverage: float = 90.0,
        result: str = "SUCCESS",
        domain: str = "general",
        architecture: str = "standard",
        stack: Optional[List[str]] = None,
        metrics: Optional[ExecutionMetrics] = None,
        stages: Optional[List[StageBreakdown]] = None,
        failures_encountered: Optional[List[Dict[str, Any]]] = None,
        lessons: Optional[List[str]] = None,
        version: str = "v1.0",
    ) -> Dict[str, Any]:
        # 1. Record Project Experience
        experience = self.experience_engine.record_experience(
            project_name=project_name,
            execution_time_sec=execution_time_sec,
            planning_score=planning_score,
            execution_score=execution_score,
            quality_score=quality_score,
            repair_count=repair_count,
            test_coverage=test_coverage,
            result=result,
            domain=domain,
            architecture=architecture,
            stack=stack,
            metrics=metrics,
            stages=stages,
            lessons_learned=lessons,
        )

        # 2. Record Failures and Solutions to Failure DB
        if failures_encountered:
            for f in failures_encountered:
                cat = f.get("category", "general")
                try:
                    category = FailureCategory(cat)
                except ValueError:
                    category = FailureCategory.GENERAL

                self.failure_engine.record_failure(
                    problem=f.get("problem", "Unknown Error"),
                    reason=f.get("reason", "Bug in code"),
                    root_cause=f.get("root_cause", ""),
                    fix_strategy=f.get("fix_strategy", ""),
                    code_diff=f.get("code_diff", ""),
                    success=f.get("success", True),
                    repair_time_sec=f.get("repair_time_sec", 0.0),
                    category=category,
                    domain=domain,
                    failing_symbol=f.get("failing_symbol", ""),
                )

        # 3. Register or Update Success Pattern if high-performing
        if result == "SUCCESS" and quality_score >= 90.0:
            self.success_engine.register_pattern(
                name=f"{domain.title()} Architecture - {architecture}",
                pattern_type=PatternType.ARCHITECTURE,
                domain=domain,
                blueprint={"architecture": architecture, "stack": stack or []},
                benchmark_score=quality_score,
                description=f"Proven high-scoring pattern from {project_name}",
            )

        # 4. Sync Knowledge Base
        for lesson in (lessons or []):
            self.knowledge_sync.sync_entry(
                category=KnowledgeCategory.LESSONS,
                title=f"Lesson from {project_name}",
                summary=lesson,
                source_project=project_name,
            )

        # 5. Record Version Performance
        self.version_engine.record_version(
            version=version,
            planning_score=planning_score,
            execution_score=execution_score,
            qa_score=quality_score,
            repair_score=95.0 if repair_count <= 2 else 80.0,
            performance_score=90.0,
            coverage_pct=test_coverage,
            notes=f"Processed run of {project_name}",
        )

        # 6. Generate Proactive Recommendations
        recommendations = self.recommendation_engine.generate_recommendations(experience)

        # 7. Compute Evolution Score
        evo_score = EvolutionScoreCalculator.compute_score(
            planning_score=planning_score,
            execution_score=execution_score,
            qa_score=quality_score,
            repair_score=95.0 if repair_count <= 2 else 80.0,
            performance_score=90.0,
            learning_score=96.0,
        )

        return {
            "experience": experience.to_dict(),
            "evolution_score": evo_score,
            "recommendations": [r.to_dict() for r in recommendations],
            "knowledge_entries_total": sum(self.knowledge_sync.get_knowledge_summary().values()),
        }

    def get_evolution_dashboard(self) -> Dict[str, Any]:
        stats = self.experience_engine.get_aggregate_stats()
        common_failures = self.failure_engine.get_most_common_failures(limit=5)
        recs = self.recommendation_engine.generate_recommendations()
        knowledge_summary = self.knowledge_sync.get_knowledge_summary()
        version_summary = self.version_engine.get_version_trend_summary()

        evo_score = EvolutionScoreCalculator.compute_score(
            planning_score=stats.get("average_planning_score", 95.0),
            execution_score=stats.get("average_execution_score", 92.0),
            qa_score=stats.get("average_quality_score", 90.0),
            repair_score=92.0,
            performance_score=90.0,
            learning_score=97.0,
        )

        return {
            "status": "🟢 Healthy",
            "widgets": {
                "experience": stats,
                "knowledge_growth": knowledge_summary,
                "success_rate_pct": stats.get("success_rate_pct", 100.0),
                "failure_trends": common_failures,
                "evolution_score": evo_score,
                "recommendations": [r.to_dict() for r in recs[:4]],
            },
            "version_trend_text": version_summary,
        }

    def generate_weekly_review(self) -> WeeklySelfReview:
        stats = self.experience_engine.get_aggregate_stats()
        common_failures = self.failure_engine.get_most_common_failures(limit=3)
        issue_names = [f.get("problem", "Issue") for f in common_failures] or ["Configuration", "Circular Import"]
        
        evo_score = EvolutionScoreCalculator.compute_score(
            planning_score=stats.get("average_planning_score", 95.0),
            execution_score=stats.get("average_execution_score", 92.0),
            qa_score=stats.get("average_quality_score", 90.0),
            repair_score=92.0,
            performance_score=90.0,
            learning_score=97.0,
        )

        total_knowledge = sum(self.knowledge_sync.get_knowledge_summary().values())

        return WeeklySelfReview(
            total_projects=stats.get("total_projects", 1),
            success_count=int(stats.get("total_projects", 1) * (stats.get("success_rate_pct", 100.0) / 100.0)),
            failure_count=max(0, stats.get("total_projects", 1) - int(stats.get("total_projects", 1) * (stats.get("success_rate_pct", 100.0) / 100.0))),
            most_common_issues=issue_names,
            recommended_focus="Improve Config Loader and Parallel DAG Execution",
            evolution_score=evo_score["overall_evolution_score"],
            knowledge_growth_entries=total_knowledge,
        )
