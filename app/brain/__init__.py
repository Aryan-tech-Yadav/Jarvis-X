"""Brain package - Engineering Intelligence Kernel (EIK).

This is the brain kernel that makes Jarvis intelligent.
Never gives direct answers - always thinks first.

Modules:
  - thinking: Problem decomposition and planning
  - decision: Plan scoring and selection
  - strategy: Execution strategy selection
  - error_intelligence: Error understanding and recovery
  - reflection: Post-task analysis
  - evolution: Controlled system improvement
  - analytics: Daily intelligence reports
  - benchmarks: Intelligence measurement
"""

from app.brain.brain_kernel import BrainKernel, BrainContext
from app.brain.thinking import ThinkingEngine, ThinkingMode, ThinkingResult, Plan, SubProblem
from app.brain.decision import DecisionEngine, DecisionScore, DecisionResult
from app.brain.strategy import StrategyEngine, Strategy, StrategyResult, StrategyType
from app.brain.error_intelligence import (
    ErrorIntelligence, ErrorAnalysis, ErrorSolution,
    ErrorKnowledgeBase, ErrorCategory,
)
from app.brain.reflection import ReflectionEngine, ReflectionReport, ReflectionInsight
from app.brain.evolution import EvolutionEngine, EvolutionReport, ImprovementProposal
from app.brain.analytics import BrainAnalytics, DailyReport
from app.brain.benchmarks import IntelligenceBenchmark, BenchmarkResult

__all__ = [
    "BrainKernel",
    "BrainContext",
    "ThinkingEngine",
    "ThinkingMode",
    "ThinkingResult",
    "Plan",
    "SubProblem",
    "DecisionEngine",
    "DecisionScore",
    "DecisionResult",
    "StrategyEngine",
    "Strategy",
    "StrategyResult",
    "StrategyType",
    "ErrorIntelligence",
    "ErrorAnalysis",
    "ErrorSolution",
    "ErrorKnowledgeBase",
    "ErrorCategory",
    "ReflectionEngine",
    "ReflectionReport",
    "ReflectionInsight",
    "EvolutionEngine",
    "EvolutionReport",
    "ImprovementProposal",
    "BrainAnalytics",
    "DailyReport",
    "IntelligenceBenchmark",
    "BenchmarkResult",
]
