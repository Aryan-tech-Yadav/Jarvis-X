from app.agents.base_agent import BaseAgent
from app.agents.agent_registry import AgentRegistry
from app.agents.research_agent import ResearchAgent
from app.agents.agent_context import AgentContext
from app.agents.agent_status import AgentStatus
from app.agents.coordinator import AgentCoordinator
from app.agents.debug_agent import DebugAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.message_bus import AgentMessage, MessageBus
from app.agents.planner_agent import PlannerAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.agent_result import AgentResult
from app.agents.capability import AgentCapability
from app.agents.coordinator_agent import CoordinatorAgent
from app.agents.shared_workspace import SharedWorkspace
from app.agents.shared_notes import SharedNotes
from app.agents.architecture_agent import ArchitectureAgent
from app.agents.health_monitor import AgentHealthMonitor
from app.agents.task import AgentTask
from app.agents.task_queue import AgentTaskQueue
from app.agents.task_scheduler import TaskScheduler
from app.agents.capability_matcher import AgentCapabilityMatcher
from app.agents.dynamic_loader import AgentLoader
from app.agents.lifecycle import AgentLifecycleManager
from app.agents.sandbox import AgentSandbox

__all__ = [
    "AgentCapability", "AgentCapabilityMatcher", "AgentContext", "AgentCoordinator",
    "AgentHealthMonitor", "AgentLoader", "AgentLifecycleManager", "AgentMessage",
    "AgentRegistry", "AgentResult", "AgentSandbox", "AgentStatus", "AgentTask",
    "AgentTaskQueue", "ArchitectureAgent", "BaseAgent", "CoderAgent", "CodingAgent",
    "CoordinatorAgent", "DebugAgent", "DocumentationAgent", "MessageBus", "PlannerAgent",
    "ResearchAgent", "ReviewerAgent", "SharedNotes", "SharedWorkspace", "TaskScheduler",
    "TesterAgent", "TestingAgent",
]

# Lazy imports to break circular dependency:
#   project_manager → planning → orchestrator → agents → coder_agent → project_manager
_LAZY_AGENTS = {
    "CoderAgent": ("app.agents.coder_agent", "CoderAgent"),
    "CodingAgent": ("app.agents.coding_agent", "CodingAgent"),
    "TesterAgent": ("app.agents.tester_agent", "TesterAgent"),
    "TestingAgent": ("app.agents.testing_agent", "TestingAgent"),
}


def __getattr__(name: str):
    if name in _LAZY_AGENTS:
        module_path, class_name = _LAZY_AGENTS[name]
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
