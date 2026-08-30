from app.architecture.architecture_engine import ArchitectureEngine
from app.governance.audit_logger import AuditLogger
from app.governance.policy_engine import PolicyEngine
from app.research.research_engine import ResearchEngine
from app.requirements.requirement_manager import RequirementManager
from app.risk.risk_engine import RiskEngine
from app.strategy.strategy_engine import StrategyEngine
from app.simulation.project_simulator import ProjectSimulator
from app.cost.cost_analyzer import CostAnalyzer
from app.optimizer.execution_optimizer import ExecutionOptimizer
from app.core.results import ExecutionResult
from app.semantic_memory.semantic_manager import SemanticMemoryManager
from app.workflow.workflow_engine import WorkflowEngine
from app.analysis.analysis_engine import AnalysisEngine


class BrainPipeline:
    """Deterministic pre-execution intelligence pipeline.

    It prepares a governed engineering brief; it deliberately does not execute
    tools or write project files. Existing orchestrators remain responsible for
    approved execution.
    """

    def __init__(self, requirements=None, architecture=None, risk=None, research=None,
                 policy=None, audit=None, strategy=None, simulator=None, cost=None,
                 execution_optimizer=None, semantic_memory=None, workflow_engine=None, analysis_engine=None):
        self.requirements = requirements or RequirementManager()
        self.architecture = architecture or ArchitectureEngine()
        self.risk = risk or RiskEngine()
        self.research = research or ResearchEngine()
        self.policy = policy or PolicyEngine()
        self.audit = audit or AuditLogger()
        self.strategy = strategy or StrategyEngine()
        self.simulator = simulator or ProjectSimulator()
        self.cost = cost or CostAnalyzer()
        self.execution_optimizer = execution_optimizer or ExecutionOptimizer()
        self.semantic_memory = semantic_memory or SemanticMemoryManager()
        self.workflow_engine = workflow_engine or WorkflowEngine()
        self.analysis_engine = analysis_engine or AnalysisEngine()

    def prepare(self, goal):
        semantic_context = self.semantic_memory.context_for(goal)
        requirements = self.requirements.analyze(goal)
        self.audit.record("requirements_analyzed", input_data={"goal": goal}, output_data=requirements,
                          confidence=self._confidence(requirements))
        architecture = self.architecture.design(requirements)
        self.audit.record("architecture_selected", input_data=requirements, output_data=architecture,
                          confidence=0.85)
        risk = self.risk.assess(requirements, architecture)
        strategy = self.strategy.choose(goal)
        simulation = self.simulator.simulate(requirements, architecture, strategy["selected"])
        workflow = self.workflow_engine.prepare(goal, requirements, risk, simulation)
        cost = self.cost.analyze(simulation)
        analysis = self.analysis_engine.analyze(goal, requirements=requirements, architecture=architecture,
                                                risk=risk, cost=cost)
        execution = self.execution_optimizer.optimize(self._execution_steps(requirements, simulation))
        research = self.research.research(requirements, architecture)
        approval = self.policy.evaluate(requirements, risk)
        self.audit.record("execution_policy_evaluated", input_data={"risk": risk}, output_data=approval,
                          confidence=1.0, risk=risk["score"])
        return {
            "goal": goal,
            "semantic_context": semantic_context,
            "workflow": workflow.to_dict(),
            "requirements": requirements,
            "architecture": architecture,
            "risk": risk,
            "strategy": strategy,
            "simulation": simulation,
            "cost": cost,
            "analysis": analysis,
            "planning_package": analysis["planning_package"],
            "execution": execution,
            "research": research,
            "approval": approval,
            "audit": self.audit.events(),
        }

    def prepare_result(self, goal):
        """Return the governed brief using the common cross-module result model."""
        result = ExecutionResult.timed(self.prepare, goal)
        if result.success:
            result.message = "Engineering brief prepared"
            result.metrics.update({
                "risk_score": result.data["risk"]["score"],
                "estimated_files": result.data["simulation"]["estimated_files"],
                "estimated_minutes": result.data["simulation"]["estimated_minutes"],
            })
        return result

    @staticmethod
    def _confidence(requirements):
        return max(0.2, round(1.0 - 0.15 * len(requirements.get("ambiguities", ())), 2))

    @staticmethod
    def _execution_steps(requirements, simulation):
        implementation_size = simulation["estimated_files"]
        return [
            {"name": "design", "estimated_files": 2},
            {"name": "implement", "dependencies": ["design"], "estimated_files": implementation_size},
            {"name": "validate", "dependencies": ["implement"], "parallelizable": True},
            {"name": "test", "dependencies": ["implement"], "parallelizable": True},
            {"name": "document", "dependencies": ["implement"], "estimated_files": 1},
        ]
