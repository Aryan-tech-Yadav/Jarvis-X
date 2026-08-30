"""Learning module for project history, improvement tracking, and pattern learning."""

from app.learning.bug_pattern import BugPattern
from app.learning.code_pattern import CodePattern
from app.learning.experience_manager import ExperienceManager
from app.learning.improvement_engine import ImprovementEngine
from app.learning.learning_database import LearningDatabase
from app.learning.learning_engine import LearningEngine
from app.learning.learning_memory import LearningMemory
from app.learning.learning_optimizer import LearningOptimizer
from app.learning.learning_report import LearningReport
from app.learning.learning_score import LearningScore
from app.learning.lesson_store import LessonStore
from app.learning.pattern_extractor import PatternExtractor
from app.learning.prompt_pattern import PromptPattern
from app.learning.project_history import ProjectHistory
from app.learning.ranking import PatternRanking
from app.learning.repair_pattern import RepairPattern
from app.learning.scorer import PatternScorer

__all__ = [
    "BugPattern",
    "CodePattern",
    "ExperienceManager",
    "ImprovementEngine",
    "LearningDatabase",
    "LearningEngine",
    "LearningMemory",
    "LearningOptimizer",
    "LearningReport",
    "LearningScore",
    "LessonStore",
    "PatternExtractor",
    "PatternRanking",
    "PatternScorer",
    "PromptPattern",
    "ProjectHistory",
    "RepairPattern",
]
