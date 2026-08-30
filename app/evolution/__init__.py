"""Autonomous Learning & Evolution Engine (ALE) package."""

from .evolution_report import EvolutionScoreCalculator, WeeklySelfReview
from .experience_engine import ExperienceEngine
from .failure_engine import FailureEngine
from .knowledge_sync import KnowledgeSync
from .learning_engine import AutonomousLearningEngine
from .models import (
    EvolutionRecommendation,
    ExecutionMetrics,
    FailureCategory,
    FailureRecord,
    KnowledgeCategory,
    KnowledgeEntry,
    Pattern,
    PatternType,
    ProjectExperience,
    RecommendationType,
    StageBreakdown,
)
from .optimization_engine import OptimizationEngine
from .recommendation_engine import RecommendationEngine
from .success_engine import SuccessPatternEngine
from .version_engine import VersionEngine
from .self_evolution_engine import AgentSkill, SelfEvolutionEngine

__all__ = [
    # Engines
    "AutonomousLearningEngine",
    "ExperienceEngine",
    "FailureEngine",
    "SuccessPatternEngine",
    "OptimizationEngine",
    "RecommendationEngine",
    "VersionEngine",
    "KnowledgeSync",
    "EvolutionScoreCalculator",
    "WeeklySelfReview",
    # Models
    "ProjectExperience",
    "ExecutionMetrics",
    "StageBreakdown",
    "Pattern",
    "PatternType",
    "FailureRecord",
    "FailureCategory",
    "KnowledgeEntry",
    "KnowledgeCategory",
    "EvolutionRecommendation",
    "RecommendationType",
    "AgentSkill",
    "SelfEvolutionEngine",
]
