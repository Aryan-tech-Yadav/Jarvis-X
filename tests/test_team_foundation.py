import tempfile
import unittest
from types import SimpleNamespace

from app.agents.agent_registry import AgentRegistry
from app.agents.agent_result import AgentResult
from app.agents.message_bus import MessageBus
from app.agents.shared_notes import SharedNotes
from app.agents.shared_workspace import SharedWorkspace
from app.agents.task_dispatcher import TaskDispatcher
from app.memory.experience_memory import ExperienceMemory
from app.memory.memory_manager import MemoryManager
from app.planning.dependency_resolver import DependencyResolver
from app.planning.goal_tree import GoalNode
from app.planning.milestone_tracker import MilestoneTracker
from app.recovery.error_classifier import ErrorClassifier
from app.recovery.retry_policy import RetryPolicy
from app.tools.tool_history import ToolCall, ToolHistory


class FakeAgent:
    def __init__(self, results):
        self.results = iter(results)

    def run(self, task):
        return next(self.results)


class TeamFoundationTests(unittest.TestCase):
    def test_dispatcher_retries_failed_agent(self):
        registry = AgentRegistry()
        registry.register("debug", FakeAgent([{"success": False}, {"success": True, "output": "fixed"}]))

        result = TaskDispatcher(registry, max_retries=1).dispatch(SimpleNamespace(agent="debug"))

        self.assertTrue(result["success"])

    def test_registry_find_best_and_lifecycle(self):
        first = FakeAgent([{"success": True}])
        first.capabilities = ["coding"]
        first.priority = 1
        second = FakeAgent([{"success": True}])
        second.capabilities = ["coding"]
        second.priority = 5
        registry = AgentRegistry()
        registry.register("one", first)
        registry.register("two", second)

        self.assertIs(registry.find_best(SimpleNamespace(agent="coding")), second)
        registry.replace("one", second)
        self.assertIs(registry.unregister("one"), second)

    def test_message_broadcast_and_reply(self):
        bus = MessageBus()
        messages = bus.broadcast("coding", ["testing", "debug"], "DONE")
        reply = bus.reply(messages[0], "testing", "ok")

        self.assertEqual(bus.receive("debug").message_type, "DONE")
        self.assertEqual(bus.receive("coding").message_type, "REPLY")
        self.assertEqual(reply.receiver, "coding")

    def test_shared_notes_workspace_and_result(self):
        notes = SharedNotes()
        notes.write("coding", "Use JWT")
        workspace = SharedWorkspace("Build API", open_issues=["tests"])
        result = AgentResult(True, files=["main.py"])

        self.assertEqual(notes.read("coding"), ["Use JWT"])
        self.assertEqual(workspace.open_issues, ["tests"])
        self.assertEqual(result.to_dict()["files"], ["main.py"])

    def test_goal_tree_dependency_and_milestone_progress(self):
        root = GoalNode("auth")
        root.add(GoalNode("login"))
        tracker = MilestoneTracker(["auth", "db"])
        tracker.complete("auth")

        self.assertEqual(len(root.flatten()), 2)
        self.assertEqual(DependencyResolver().order(["api", "db"], {"api": ["db"]}), ["db", "api"])
        self.assertEqual(tracker.progress()["percent"], 50.0)

    def test_memory_tool_history_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = MemoryManager()
            memory.file = f"{directory}/memory.json"
            experience = ExperienceMemory(memory)
            experience.save({"goal": "Build API"})
            experience.save({"goal": "Build API"})
            self.assertEqual(len(experience.find("api")), 1)

        history = ToolHistory()
        history.record(ToolCall("terminal", 0.1, True))
        self.assertEqual(len(history.list()), 1)
        self.assertEqual(ErrorClassifier().classify("Module import failed"), "import")
        self.assertTrue(RetryPolicy().can_retry("runtime", 3))


if __name__ == "__main__":
    unittest.main()