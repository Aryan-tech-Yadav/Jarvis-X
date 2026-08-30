"""Autonomous Experience Engine for recording, aggregating, and recalling project executions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models.experience import ExecutionMetrics, ProjectExperience, StageBreakdown


class ExperienceEngine:
    """Stores every project run, building Jarvis-X's institutional engineering memory."""

    def __init__(self, knowledge_dir: Optional[str] = None):
        self.knowledge_dir = Path(knowledge_dir).resolve() if knowledge_dir else (Path.cwd() / "knowledge")
        self.experience_dir = self.knowledge_dir / "experience"
        self.experience_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.experience_dir / "experience_store.json"
        self._experiences: List[ProjectExperience] = self._load()

    def _load(self) -> List[ProjectExperience]:
        if not self.store_file.exists():
            return []
        try:
            data = json.loads(self.store_file.read_text(encoding="utf-8"))
            records = []
            for item in data:
                metrics_data = item.get("metrics", {})
                metrics = ExecutionMetrics(**metrics_data) if isinstance(metrics_data, dict) else ExecutionMetrics()
                stages = [StageBreakdown(**s) for s in item.get("stages", []) if isinstance(s, dict)]
                item_copy = dict(item)
                item_copy["metrics"] = metrics
                item_copy["stages"] = stages
                records.append(ProjectExperience(**item_copy))
            return records
        except Exception:
            return []

    def _save(self):
        try:
            payload = [exp.to_dict() for exp in self._experiences]
            self.store_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass

    def record_experience(
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
        lessons_learned: Optional[List[str]] = None,
    ) -> ProjectExperience:
        m = metrics or ExecutionMetrics(total_time_sec=execution_time_sec)
        m.total_time_sec = execution_time_sec

        exp = ProjectExperience(
            project_name=project_name,
            domain=domain,
            architecture=architecture,
            stack=stack or ["python", "fastapi"],
            planning_score=planning_score,
            execution_score=execution_score,
            quality_score=quality_score,
            repair_count=repair_count,
            test_coverage=test_coverage,
            result=result,
            metrics=m,
            stages=stages or [],
            lessons_learned=lessons_learned or [],
        )
        self._experiences.append(exp)
        self._save()
        return exp

    def query_experiences(
        self,
        domain: Optional[str] = None,
        architecture: Optional[str] = None,
        min_quality: float = 0.0,
        limit: int = 10,
    ) -> List[ProjectExperience]:
        results = []
        for exp in reversed(self._experiences):
            if domain and exp.domain.lower() != domain.lower():
                continue
            if architecture and exp.architecture.lower() != architecture.lower():
                continue
            if exp.quality_score < min_quality:
                continue
            results.append(exp)
            if len(results) >= limit:
                break
        return results

    def get_aggregate_stats(self) -> Dict[str, Any]:
        total = len(self._experiences)
        if total == 0:
            return {
                "total_projects": 0,
                "success_rate_pct": 100.0,
                "average_planning_score": 0.0,
                "average_execution_score": 0.0,
                "average_quality_score": 0.0,
                "average_coverage_pct": 0.0,
                "total_repairs": 0,
                "average_runtime_sec": 0.0,
            }

        successful = len([e for e in self._experiences if e.result == "SUCCESS"])
        avg_planning = sum(e.planning_score for e in self._experiences) / total
        avg_exec = sum(e.execution_score for e in self._experiences) / total
        avg_qual = sum(e.quality_score for e in self._experiences) / total
        avg_cov = sum(e.test_coverage for e in self._experiences) / total
        total_rep = sum(e.repair_count for e in self._experiences)
        avg_run = sum(e.metrics.total_time_sec for e in self._experiences) / total

        return {
            "total_projects": total,
            "success_rate_pct": round((successful / total) * 100.0, 2),
            "average_planning_score": round(avg_planning, 2),
            "average_execution_score": round(avg_exec, 2),
            "average_quality_score": round(avg_qual, 2),
            "average_coverage_pct": round(avg_cov, 2),
            "total_repairs": total_rep,
            "average_runtime_sec": round(avg_run, 2),
        }
