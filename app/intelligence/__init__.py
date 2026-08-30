"""Jarvis-X Intelligence Layer.

Provides self-improvement and experience-driven engineering:
  - ExperienceEngine: records project execution experiences
  - ProjectMemoryStore: structured project memory
  - KnowledgeGraph: graph of engineering concepts and relationships
  - BenchmarkEngine: multi-dimensional project scoring
  - SelfImprover: automatic pattern improvement based on outcomes
  - SimilarityEngine: find similar projects for reuse
  - EngineeringMemory: store mistakes, fixes, libraries, tricks
  - PatternLibrary: reusable engineering patterns
  - PromptOptimizer: optimize prompts based on execution scores
"""

from app.intelligence.experience_engine import ExperienceEngine, ProjectExperience
from app.intelligence.project_memory import ProjectMemoryStore, ProjectMemory
from app.intelligence.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge
from app.intelligence.benchmark_engine import BenchmarkEngine, BenchmarkScore, BenchmarkReport
from app.intelligence.self_improver import SelfImprover, Improvement
from app.intelligence.similarity_engine import SimilarityEngine, SimilarityResult
from app.intelligence.engineering_memory import EngineeringMemory, EngineeringMemoryEntry
from app.intelligence.pattern_library import PatternLibrary, EngineeringPattern
from app.intelligence.prompt_optimizer import PromptOptimizer, PromptVersion

__all__ = [
    "ExperienceEngine",
    "ProjectExperience",
    "ProjectMemoryStore",
    "ProjectMemory",
    "KnowledgeGraph",
    "GraphNode",
    "GraphEdge",
    "BenchmarkEngine",
    "BenchmarkScore",
    "BenchmarkReport",
    "SelfImprover",
    "Improvement",
    "SimilarityEngine",
    "SimilarityResult",
    "EngineeringMemory",
    "EngineeringMemoryEntry",
    "PatternLibrary",
    "EngineeringPattern",
    "PromptOptimizer",
    "PromptVersion",
]
from .constitution import (
    ConfidenceEngine,
    ConstitutionDecision,
    EngineeringConstitution,
    Principle,
)
from .meta_engineering import (
    ImprovementProposal,
    MetaCognitionReview,
    MetaEngineeringEngine,
    UncertaintyAssessment,
)

__all__ += [
    "ConfidenceEngine",
    "ConstitutionDecision",
    "EngineeringConstitution",
    "Principle",
    "MetaEngineeringEngine",
    "MetaCognitionReview",
    "UncertaintyAssessment",
    "ImprovementProposal",
]
