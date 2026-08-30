"""Self-evolution engine v1.0.

Orchestrates the full self-improvement lifecycle:
  Analyze -> Plan -> Risk -> Sandbox -> Improve -> Test -> Benchmark -> Review -> Accept
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.self_improvement.analyzer import SystemAnalyzer
from app.self_improvement.benchmark import BenchmarkEngine
from app.self_improvement.comparator import BenchmarkComparator
from app.self_improvement.dependency_graph import DependencyGraphBuilder
from app.self_improvement.evolution_db import EvolutionDB
from app.self_improvement.planner import ImprovementPlanner
from app.self_improvement.project_scanner import ProjectScanner
from app.self_improvement.quality_checker import QualityChecker
from app.self_improvement.risk_engine import RiskEngine
from app.self_improvement.sandbox import SandboxBuilder
from app.self_improvement.version_manager import VersionManager
from app.self_improvement.reviewer import AICodeReviewer


class SelfEvolutionEngine:
    """Orchestrate the self-improvement lifecycle."""

    def __init__(
        self,
        project_path: str = ".",
        sandboxes_root: str = ".sandboxes",
        versions_root: str = ".versions",
        db_path: str = "data/evolution.db",
    ):
        self.project_path = os.path.abspath(project_path)
        self.project_scanner = ProjectScanner(self.project_path)
        self.dependency_builder = DependencyGraphBuilder(self.project_path)
        self.quality_checker = QualityChecker(self.project_path)
        self.analyzer = SystemAnalyzer(self.project_path)
        self.planner = ImprovementPlanner()
        self.risk_engine = RiskEngine()
        self.benchmark_engine = BenchmarkEngine(self.project_path)
        self.comparator = BenchmarkComparator()
        self.code_reviewer = AICodeReviewer()
        self.sandbox_builder = SandboxBuilder(sandboxes_root)
        self.version_manager = VersionManager(versions_root)
        self.evolution_db = EvolutionDB(db_path)

    def evolve(self, max_improvements: int = 5, require_approval: bool = True) -> ExecutionResult:
        """Run the full self-evolution loop."""
        started = time.perf_counter()
        Logger.info("[SelfEvolutionEngine] Starting self-evolution")

        # Phase 1: Scan project
        scan_result = self.project_scanner.scan()
        Logger.info(f"[SelfEvolutionEngine] Scan complete: {scan_result.files} files, {scan_result.functions} functions")

        # Phase 2: Build dependency graph
        dep_graph = self.dependency_builder.build()
        if dep_graph.cycles:
            Logger.warning(f"[SelfEvolutionEngine] Found {len(dep_graph.cycles)} circular dependencies")

        # Phase 3: Quality check
        quality_reports = self.quality_checker.check_project()
        low_quality_files = [r for r in quality_reports if r.maintainability < 70]
        Logger.info(f"[SelfEvolutionEngine] Quality check: {len(low_quality_files)} files need improvement")

        # Phase 4: Full analysis
        analysis = self.analyzer.analyze()
        analysis_dict = analysis.to_dict()

        # Phase 5: Create improvement plan
        plan = self.planner.create_plan(analysis_dict)
        Logger.info(f"[SelfEvolutionEngine] Plan: {len(plan.high_priority)} high, {len(plan.medium_priority)} medium, {len(plan.low_priority)} low")

        # Phase 6: Baseline benchmark
        baseline = self.benchmark_engine.run_benchmark(self.project_path, version="baseline")

        # Phase 7: Create version snapshot
        version = self.version_manager.create_version(self.project_path, score=baseline.quality_score)

        all_tasks = plan.high_priority + plan.medium_priority + plan.low_priority
        applied_improvements = []
        rejected_improvements = []

        for task in all_tasks[:max_improvements]:
            # Phase 8: Risk assessment
            risk_assessment = self.risk_engine.assess(task.to_dict())

            if require_approval and risk_assessment.requires_approval:
                Logger.warning(f"[SelfEvolutionEngine] Skipping {task.id}: requires approval (risk: {risk_assessment.risk_level})")
                rejected_improvements.append({
                    "task": task.to_dict(),
                    "reason": "Requires manual approval",
                    "risk": risk_assessment.to_dict(),
                })
                continue

            # Phase 9: Create sandbox
            sandbox = self.sandbox_builder.create(self.project_path, task.id)

            # Phase 10: Benchmark sandbox
            sandbox_benchmark = self.benchmark_engine.run_benchmark(sandbox.sandbox_path, version=f"sandbox-{task.id}")

            # Phase 11: Compare
            comparison = self.comparator.compare(baseline.to_dict(), sandbox_benchmark.to_dict())

            # Phase 12: Code review if changes exist
            review = None
            file_path = task.file
            if file_path:
                src = os.path.join(self.project_path, file_path)
                dst = os.path.join(sandbox.sandbox_path, file_path)
                if os.path.exists(src) and os.path.exists(dst):
                    try:
                        with open(src, "r", encoding="utf-8", errors="replace") as f:
                            original_content = f.read()
                        with open(dst, "r", encoding="utf-8", errors="replace") as f:
                            modified_content = f.read()
                        if original_content != modified_content:
                            review = self.code_reviewer.review(original_content, modified_content, file_path)
                    except (OSError, UnicodeDecodeError):
                        pass

            # Phase 13: Decision
            recommendation = comparison.get("recommendation", "REVIEW")
            accepted = recommendation in ("STRONG_ACCEPT", "ACCEPT")

            if accepted:
                self.sandbox_builder.promote(sandbox.sandbox_id, self.project_path)
                applied_improvements.append({
                    "task": task.to_dict(),
                    "benchmark_comparison": comparison,
                    "review": review.to_dict() if review else None,
                    "sandbox_id": sandbox.sandbox_id,
                })
            else:
                self.sandbox_builder.discard(sandbox.sandbox_id)
                rejected_improvements.append({
                    "task": task.to_dict(),
                    "reason": f"Benchmark: {recommendation}",
                    "benchmark_comparison": comparison,
                    "review": review.to_dict() if review else None,
                })

        # Phase 14: Record evolution
        duration = time.perf_counter() - started
        final_benchmark = self.benchmark_engine.run_benchmark(self.project_path, version="final")
        evolution_id = self.evolution_db.record_evolution(
            plan=plan.to_dict(),
            baseline=baseline.to_dict(),
            applied=applied_improvements,
            rejected=rejected_improvements,
            duration=duration,
        )
        self.version_manager.archive(version.version_id)

        Logger.success(f"[SelfEvolutionEngine] Evolution complete: {len(applied_improvements)} applied, {len(rejected_improvements)} rejected")

        return ExecutionResult(
            success=True,
            status="completed",
            message=f"Self-evolution complete: {len(applied_improvements)} improvements applied",
            data={
                "evolution_id": evolution_id,
                "version_id": version.version_id,
                "scan": scan_result.to_dict(),
                "dependency_graph": dep_graph.to_dict(),
                "quality_reports": [r.to_dict() for r in quality_reports[:10]],
                "plan": plan.to_dict(),
                "baseline": baseline.to_dict(),
                "final": final_benchmark.to_dict(),
                "applied": applied_improvements,
                "rejected": rejected_improvements,
                "comparison": self.comparator.compare(baseline.to_dict(), final_benchmark.to_dict()),
            },
            metrics={
                "duration": round(duration, 3),
                "applied": len(applied_improvements),
                "rejected": len(rejected_improvements),
                "final_score": final_benchmark.quality_score,
                "files_scanned": scan_result.files,
                "cycles_detected": len(dep_graph.cycles),
            },
            duration=duration,
        )

    def analyze_only(self) -> ExecutionResult:
        """Run analysis without modifications."""
        started = time.perf_counter()

        scan_result = self.project_scanner.scan()
        dep_graph = self.dependency_builder.build()
        quality_reports = self.quality_checker.check_project()
        analysis = self.analyzer.analyze()
        plan = self.planner.create_plan(analysis.to_dict())

        duration = time.perf_counter() - started
        return ExecutionResult(
            success=True,
            status="completed",
            message="System analysis complete",
            data={
                "scan": scan_result.to_dict(),
                "dependency_graph": dep_graph.to_dict(),
                "quality_reports": [r.to_dict() for r in quality_reports[:10]],
                "analysis": analysis.to_dict(),
                "plan": plan.to_dict(),
            },
            metrics={"duration": round(duration, 3), "opportunities": len(analysis.improvement_opportunities)},
            duration=duration,
        )

    execute = evolve
