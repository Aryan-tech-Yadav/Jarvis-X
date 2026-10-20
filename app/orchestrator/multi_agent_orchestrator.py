from app.agents.agent_registry import AgentRegistry
from app.agents.base_agent import BaseAgent
from app.agents.research_agent import ResearchAgent
from app.core.logger import Logger
from app.project.project_analyzer import ProjectAnalyzer
from app.project.project_builder import ProjectBuilder
from app.project.project_planner import ProjectPlanner
from app.project.project_repair_manager import ProjectRepairManager
from app.project.project_validator import ProjectValidator
from app.learning.learning_engine import LearningEngine
from app.orchestrator.shared_context import SharedContext


PIPELINE = ("researcher", "planner", "analyzer", "coder", "reviewer", "critic", "validator", "repair")


class MultiAgentOrchestrator:
    def __init__(self, registry=None, max_repairs=2, learning_engine=None):
        self.registry = registry or self._default_registry()
        self.max_repairs = max(0, max_repairs)
        self.learning_engine = learning_engine or LearningEngine()

    def run(self, goal, base_path=None, context=None):
        if context is None:
            if not isinstance(goal, str) or not goal.strip():
                raise ValueError("Goal cannot be empty")
            context = SharedContext(goal=goal.strip(), base_path=base_path)
        elif not isinstance(context, SharedContext):
            raise TypeError("context must be a SharedContext")

        current = "researcher"
        repairs = 0
        review_after_repair = False
        while current:
            agent = self.registry.get(current)
            if agent is None:
                return self._failure(context, current, f"Agent not registered: {current}")

            Logger.info(f"[{current.title()}] Starting")
            try:
                result = agent.run(context)
            except Exception as error:
                result = {"success": False, "output": str(error), "error": str(error)}

            if not isinstance(result, dict):
                result = {"success": False, "output": "Agent returned an invalid result"}
            if result.get("success", False):
                result.setdefault("next_agent", self._next(current))
            context.add_progress(current, result)

            if not result.get("success", False):
                if current == "validator" and repairs < self.max_repairs:
                    current = "repair"
                    continue
                return self._failure(context, current, result.get("output", "Agent failed"))

            if current == "validator":
                context.validation = result
            if current == "critic":
                context.critic = result
            if current == "repair":
                repairs += 1
                review_after_repair = True
                current = "validator"
                continue

            if current == "validator" and review_after_repair:
                review_after_repair = False
                current = "reviewer"
                continue

            if current == "validator":
                break

            current = result.get("next_agent") or self._next(current)
            if current == "complete":
                break

        context.learning = self.learning_engine.learn(context, success=True)
        return {"success": True, "output": "Pipeline complete", "context": context, "learning": context.learning}

    def _next(self, current):
        index = PIPELINE.index(current)
        return PIPELINE[index + 1] if index + 1 < len(PIPELINE) else "complete"

    def _failure(self, context, agent, output):
        return {"success": False, "failed_agent": agent, "output": output, "context": context}

    def _default_registry(self):
        registry = AgentRegistry()
        registry.register("researcher", ResearchAgent())
        registry.register("planner", PlannerAgent())
        registry.register("analyzer", AnalyzerAgent())
        registry.register("coder", CoderAgent())
        registry.register("reviewer", ReviewerAgent())
        registry.register("critic", CriticAgent())
        registry.register("validator", ValidatorAgent())
        registry.register("repair", RepairAgent())
        return registry


class PlannerAgent(BaseAgent):
    name = "planner"

    def __init__(self, planner=None):
        self.planner = planner or ProjectPlanner()

    def run(self, context):
        plan = self.planner.plan(context.goal)
        if plan is None:
            return {"success": False, "output": "Planner did not return a plan"}
        context.plan = plan
        if isinstance(plan, dict):
            context.project = plan
        return {"success": True, "output": plan}


class AnalyzerAgent(BaseAgent):
    name = "analyzer"

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or ProjectAnalyzer()

    def run(self, context):
        if not context.base_path:
            return {"success": True, "output": "No existing project to analyze"}
        analysis = self.analyzer.analyze(context.base_path)
        context.files = analysis.get("files", [])
        return {"success": not bool(analysis.get("errors")), "output": analysis}


class CoderAgent(BaseAgent):
    name = "coder"

    def __init__(self, builder=None):
        self.builder = builder or ProjectBuilder()

    def run(self, context):
        context.base_path = self.builder.build(context.goal)
        return {"success": bool(context.base_path), "output": context.base_path}


class ReviewerAgent(AnalyzerAgent):
    name = "reviewer"


class CriticAgent(BaseAgent):
    name = "critic"

    def run(self, context):
        analysis = context.outputs.get("reviewer", {})
        issues = analysis.get("errors", []) if isinstance(analysis, dict) else []
        result = {"approved": not issues, "issues": issues, "score": 10 if not issues else 0}
        context.critic = result
        return {"success": True, "output": result}


class ValidatorAgent(BaseAgent):
    name = "validator"

    def __init__(self, validator=None):
        self.validator = validator or ProjectValidator()

    def run(self, context):
        if not context.base_path or not context.project:
            result = {"success": True, "output": "Validation deferred: no generated project"}
            context.validation = result
            return result
        valid, message = self.validator.validate(context.project, context.base_path)
        result = {"success": valid, "output": message, "valid": valid}
        context.validation = result
        return result


class RepairAgent(BaseAgent):
    name = "repair"

    def __init__(self, repair_manager=None):
        self.repair_manager = repair_manager or ProjectRepairManager()

    def run(self, context):
        if not context.base_path or not context.project:
            return {"success": False, "output": "Repair requires a project and base path"}
        message = context.validation.get("output", "")
        repaired = self.repair_manager.repair(context.project, context.base_path, message)
        return {"success": True, "output": repaired}