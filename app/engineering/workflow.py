"""Engineering workflow orchestrator.

Coordinates all engineering workflow modules to transform
a user requirement into a complete engineering plan:
  RequirementAnalyzer → QuestionGenerator → ArchitectureDesigner
  → TaskBreakdown → DependencyResolver → ExecutionPlanner
  → ProjectState → EngineeringReport
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from app.core.logger import Logger
from app.engineering.architecture_designer import ArchitectureDesigner, SystemArchitecture
from app.engineering.complexity_estimator import ComplexityEstimate, ComplexityEstimator
from app.engineering.dependency_resolver import DependencyResolver, ResolvedDependencies
from app.engineering.engineering_memory import EngineeringMemory, ProjectMemory
from app.engineering.engineering_report import EngineeringReport, EngineeringReportGenerator
from app.engineering.execution_planner import ExecutionPlan, ExecutionPlanner
from app.engineering.pattern_selector import PatternSelection, PatternSelector
from app.engineering.project_planner import ProjectPlanner
from app.engineering.project_state import ProjectStateManager
from app.engineering.question_generator import QuestionGenerator, QuestionSet
from app.engineering.requirement_analyzer import RequirementAnalyzer, RequirementAnalysis
from app.engineering.risk_analyzer import RiskAnalyzer, RiskReport
from app.engineering.task_breakdown import TaskBreakdown, TaskBreakdownEngine
from app.engineering.technology_selector import TechnologySelector, TechnologyStack


@dataclass
class EngineeringWorkflowResult:
    """Result of complete engineering workflow."""

    workflow_id: str
    requirement: str
    analysis: Optional[dict] = None
    questions: Optional[dict] = None
    architecture: Optional[dict] = None
    task_breakdown: Optional[dict] = None
    dependencies: Optional[dict] = None
    execution_plan: Optional[dict] = None
    project_state: Optional[dict] = None
    report: Optional[dict] = None
    tech_stack: Optional[dict] = None
    patterns: Optional[list] = None
    risks: Optional[dict] = None
    complexity: Optional[dict] = None
    duration: float = 0.0
    success: bool = False

    def to_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "requirement": self.requirement,
            "analysis": self.analysis,
            "questions": self.questions,
            "architecture": self.architecture,
            "task_breakdown": self.task_breakdown,
            "dependencies": self.dependencies,
            "execution_plan": self.execution_plan,
            "project_state": self.project_state,
            "report": self.report,
            "tech_stack": self.tech_stack,
            "patterns": self.patterns,
            "risks": self.risks,
            "complexity": self.complexity,
            "duration": round(self.duration, 2),
            "success": self.success,
        }


class EngineeringWorkflow:
    """Orchestrate the complete engineering workflow.

    Transforms a natural language requirement into a structured
    engineering plan with architecture, tasks, phases, and report.
    """

    def __init__(self, state_dir: str = ".jarvis/states"):
        self.analyzer = RequirementAnalyzer()
        self.question_gen = QuestionGenerator()
        self.arch_designer = ArchitectureDesigner()
        self.task_engine = TaskBreakdownEngine()
        self.dep_resolver = DependencyResolver()
        self.exec_planner = ExecutionPlanner()
        self.state_manager = ProjectStateManager(state_dir)
        self.report_gen = EngineeringReportGenerator()
        self.tech_selector = TechnologySelector()
        self.pattern_selector = PatternSelector()
        self.risk_analyzer = RiskAnalyzer()
        self.complexity_estimator = ComplexityEstimator()

    def run(self, requirement: str, ask_questions: bool = False) -> EngineeringWorkflowResult:
        """Run complete engineering workflow.

        Args:
            requirement: Natural language project requirement.
            ask_questions: Whether to generate clarifying questions.

        Returns:
            EngineeringWorkflowResult with complete plan.
        """
        workflow_id = f"eng-{uuid.uuid4().hex[:12]}"
        started = time.perf_counter()
        Logger.info(f"[EngineeringWorkflow] Starting workflow {workflow_id}")
        Logger.info(f"[EngineeringWorkflow] Requirement: {requirement[:100]}")

        try:
            # Phase 1: Analyze requirements
            Logger.info("[EngineeringWorkflow] Phase 1: Analyzing requirements")
            analysis = self.analyzer.analyze(requirement)
            Logger.success(f"[EngineeringWorkflow] Domain: {analysis.domain}, Type: {analysis.project_type}, Confidence: {analysis.confidence:.2f}")

            # Phase 2: Generate questions if needed
            questions = None
            if ask_questions and analysis.missing_information:
                Logger.info("[EngineeringWorkflow] Phase 2: Generating clarifying questions")
                questions = self.question_gen.generate(analysis)
                Logger.info(f"[EngineeringWorkflow] Generated {questions.total} questions ({questions.required} required)")

            # Phase 3: Design architecture
            Logger.info("[EngineeringWorkflow] Phase 3: Designing architecture")
            architecture = self.arch_designer.design(requirement, analysis)
            Logger.success(f"[EngineeringWorkflow] Architecture: {len(architecture.components)} components, {len(architecture.layers)} layers")

            # Phase 4: Break down into tasks
            Logger.info("[EngineeringWorkflow] Phase 4: Breaking down into tasks")
            task_breakdown = self.task_engine.breakdown(architecture, analysis)
            Logger.info(f"[EngineeringWorkflow] Tasks: {task_breakdown.total_tasks}, Est: {task_breakdown.total_estimated_hours:.1f}h")

            # Phase 5: Resolve dependencies
            Logger.info("[EngineeringWorkflow] Phase 5: Resolving dependencies")
            tasks_dict = [t.to_dict() for t in task_breakdown.tasks]
            resolved_deps = self.dep_resolver.resolve(tasks_dict)
            if resolved_deps.has_cycles:
                Logger.warning("[EngineeringWorkflow] Circular dependencies detected!")
            else:
                Logger.success(f"[EngineeringWorkflow] Dependencies resolved: {len(resolved_deps.parallel_groups)} parallel groups")

            # Phase 6: Create execution plan
            Logger.info("[EngineeringWorkflow] Phase 6: Creating execution plan")
            execution_plan = self.exec_planner.plan(task_breakdown, resolved_deps)
            Logger.success(f"[EngineeringWorkflow] Execution plan: {execution_plan.total_phases} phases")

            # Phase 7: Initialize project state
            Logger.info("[EngineeringWorkflow] Phase 7: Initializing project state")
            task_ids = [t.id for t in task_breakdown.tasks]
            project_state = self.state_manager.create_project(workflow_id, requirement[:50], task_ids)
            Logger.info(f"[EngineeringWorkflow] Project state created: {project_state.project_id}")

            # Phase 8: Select technologies
            Logger.info("[EngineeringWorkflow] Phase 8: Selecting technologies")
            tech_stack = self.tech_selector.select(analysis.to_dict())
            Logger.success(f"[EngineeringWorkflow] Tech stack: {tech_stack.backend} + {tech_stack.database}")

            # Phase 9: Select patterns
            Logger.info("[EngineeringWorkflow] Phase 9: Selecting design patterns")
            patterns = self.pattern_selector.select(analysis.to_dict())
            Logger.success(f"[EngineeringWorkflow] Patterns: {[p.pattern for p in patterns[:3]]}")

            # Phase 10: Analyze risks
            Logger.info("[EngineeringWorkflow] Phase 10: Analyzing risks")
            risk_report = self.risk_analyzer.analyze(analysis.to_dict(), architecture.to_dict())
            Logger.success(f"[EngineeringWorkflow] Risk level: {risk_report.overall_risk_level}")

            # Phase 11: Estimate complexity
            Logger.info("[EngineeringWorkflow] Phase 11: Estimating complexity")
            complexity = self.complexity_estimator.estimate(analysis.to_dict(), architecture.to_dict())
            Logger.success(f"[EngineeringWorkflow] Complexity: {complexity.complexity_score:.1f}/10, Est: {complexity.estimated_hours:.1f}h")

            # Phase 12: Generate engineering report
            Logger.info("[EngineeringWorkflow] Phase 12: Generating engineering report")
            report = self.report_gen.generate(
                requirement, analysis, architecture, task_breakdown,
                resolved_deps, execution_plan, project_state,
                tech_stack=tech_stack,
                patterns=patterns,
                risk_report=risk_report,
                complexity=complexity,
            )
            Logger.success(f"[EngineeringWorkflow] Report: Readiness {report.overall_readiness:.1f}%, Risk {report.risk_level}")

            duration = time.perf_counter() - started
            Logger.success(f"[EngineeringWorkflow] Workflow {workflow_id} complete in {duration:.2f}s")

            return EngineeringWorkflowResult(
                workflow_id=workflow_id,
                requirement=requirement,
                analysis=analysis.to_dict(),
                questions=questions.to_dict() if questions else None,
                architecture=architecture.to_dict(),
                task_breakdown=task_breakdown.to_dict(),
                dependencies=resolved_deps.to_dict(),
                execution_plan=execution_plan.to_dict(),
                project_state=project_state.to_dict(),
                report=report.to_dict(),
                tech_stack=tech_stack.to_dict(),
                patterns=[p.to_dict() for p in patterns],
                risks=risk_report.to_dict(),
                complexity=complexity.to_dict(),
                duration=duration,
                success=True,
            )

        except Exception as exc:
            duration = time.perf_counter() - started
            Logger.error(f"[EngineeringWorkflow] Workflow failed: {exc}")
            return EngineeringWorkflowResult(
                workflow_id=workflow_id,
                requirement=requirement,
                duration=duration,
                success=False,
            )

    def get_project_state(self, project_id: str) -> Optional[dict]:
        """Get current project state."""
        state = self.state_manager.get_state(project_id)
        return state.to_dict() if state else None
