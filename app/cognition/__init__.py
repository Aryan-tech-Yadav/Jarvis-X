"""Cognitive Operating System contracts, independent from EOS execution."""

from .perception import Perception, PerceptionEngine
from .attention import AttentionItem, AttentionEngine
from .goals import Goal, GoalStack, GoalStatus
from .decision import CognitiveDecision, CognitiveDecisionEngine
from .cos import CognitiveOperatingSystem
from .orchestrator import CognitiveOrchestrator, CognitivePlan, WorkingMemory

__all__ = [
    "Perception", "PerceptionEngine", "AttentionItem", "AttentionEngine",
    "Goal", "GoalStack", "GoalStatus", "CognitiveDecision",
    "CognitiveDecisionEngine", "CognitiveOperatingSystem",
    "CognitiveOrchestrator", "CognitivePlan", "WorkingMemory",
]
