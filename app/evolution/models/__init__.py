"""Evolution models package."""

from .experience import ExecutionMetrics, ProjectExperience, StageBreakdown
from .failure import FailureCategory, FailureRecord
from .knowledge import KnowledgeCategory, KnowledgeEntry
from .pattern import Pattern, PatternType
from .recommendation import EvolutionRecommendation, RecommendationType

__all__ = [
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
]
