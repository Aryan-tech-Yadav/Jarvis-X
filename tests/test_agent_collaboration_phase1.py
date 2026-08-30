import os
import tempfile
import unittest

from app.agents.agent_registry import AgentRegistry
from app.agents.coder_agent import CoderAgent
from app.agents.documentation_agent import DocumentationAgent
from app.agents.message_bus import MessageBus
from app.agents.planner_agent import PlannerAgent
from app.agents.reviewer_agent import ReviewerAgent
from app.agents.task import AgentTask
from app.agents.task_queue import AgentTaskQueue
from app.agents.tester_agent import TesterAgent
from app.orchestrator.agent_orchestrator import AgentOrchestrator
from app.orchestrator.shared_context import SharedContext


class FakeManager:
    def __init__(self, valid=True):
        self.valid = valid
        self.calls = []

    def create_project(self, goal):
        self.calls.append(("create", goal))
        return "/project"

    def modify_project(self, path, request):
        self.calls.append(("modify", path, request))
        return True, ["main.py"]

    def repair_project(self, path, request):
        self.calls.append(("repair", path, request))
        return ["main.py"]

    def validate_project(self, path):
        self.calls.append(("validate", path))
        return self.valid, "passed" if self.valid else "broken import\nmissing main.py"


class FakeAgent:
    def __init__(self, *results):
        self.results = list(results)
        self.contexts = []

    def execute(self, context):
        self.contexts.append(context)
        return self.results.pop(0)


def registry_with(**agents):
    registry = AgentRegistry()
    for name, agent in agents.items():
        registry.register(name, agent)
    return registry


class AgentCollaborationPhaseOneTests(unittest.TestCase):
    def test_base_contract_name_and_capability(self):
        agent = PlannerAgent()
        self.assertEqual(agent.name(), "planner")
        self.assertTrue(agent.can_handle({"type": "planning"}))

    def test_registry_registers_agent_instance(self):
        registry = AgentRegistry()
        planner = PlannerAgent()
        registry.register(planner)
        self.assertIs(registry.get("planner"), planner)

    def test_registry_find_uses_capability(self):
        registry = AgentRegistry()
        registry.register(PlannerAgent())
        self.assertIsInstance(registry.find({"type": "planning"}), PlannerAgent)

    def test_planner_returns_a_high_level_plan(self):
        result = PlannerAgent().execute({"goal": "Create Instagram Clone"})
        self.assertTrue(result["success"])
        self.assertGreaterEqual(len(result["output"]), 3)

    def test_planner_accepts_a_planning_dependency(self):
        result = PlannerAgent(planner=lambda goal: [goal, "tests"]).execute({"goal": "Build API"})
        self.assertEqual(result["output"], ["Build API", "tests"])

    def test_coder_delegates_project_creation(self):
        manager = FakeManager()
        context = {"goal": "Build API", "operation": "create"}
        result = CoderAgent(manager).execute(context)
        self.assertTrue(result["success"])
        self.assertEqual(context["project_path"], "/project")
        self.assertEqual(manager.calls[0], ("create", "Build API"))

    def test_coder_delegates_modification(self):
        manager = FakeManager()
        result = CoderAgent(manager).execute({"goal": "Build API", "project_path": "/project", "operation": "modify", "request": "Add login"})
        self.assertTrue(result["success"])
        self.assertEqual(manager.calls[0], ("modify", "/project", "Add login"))

    def test_coder_delegates_repair(self):
        manager = FakeManager()
        result = CoderAgent(manager).execute({"goal": "Build API", "project_path": "/project", "operation": "repair", "repair_request": "fix test"})
        self.assertTrue(result["success"])
        self.assertEqual(manager.calls[0], ("repair", "/project", "fix test"))

    def test_tester_normalizes_a_passed_validation(self):
        result = TesterAgent(FakeManager(valid=True)).execute({"project_path": "/project"})
        self.assertEqual(result["output"], {"passed": True, "errors": []})

    def test_tester_normalizes_validation_errors(self):
        result = TesterAgent(FakeManager(valid=False)).execute({"project_path": "/project"})
        self.assertFalse(result["success"])
        self.assertEqual(result["output"]["errors"], ["broken import", "missing main.py"])

    def test_reviewer_approves_safe_python_project(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "main.py"), "w", encoding="utf-8") as file:
                file.write("def main():\n    return 1\n")
            result = ReviewerAgent().execute({"project_path": directory})
        self.assertTrue(result["success"])
        self.assertTrue(result["output"]["approved"])

    def test_reviewer_reports_unsafe_dynamic_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "main.py"), "w", encoding="utf-8") as file:
                file.write("eval('1 + 1')\n")
            result = ReviewerAgent().execute({"project_path": directory})
        self.assertFalse(result["success"])
        self.assertIn("unsafe", result["output"]["issues"][0])

    def test_documentation_agent_updates_all_documentation_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            result = DocumentationAgent().execute({"project_path": directory, "goal": "Add login"})
            self.assertTrue(result["success"])
            self.assertTrue(os.path.isfile(os.path.join(directory, "README.md")))
            self.assertTrue(os.path.isfile(os.path.join(directory, "CHANGELOG.md")))
            self.assertTrue(os.path.isfile(os.path.join(directory, "docs", "latest-feature.md")))

    def test_documentation_agent_skips_without_a_project(self):
        result = DocumentationAgent().execute({"goal": "Add login"})
        self.assertTrue(result["success"])
        self.assertTrue(result["output"]["skipped"])

    def test_message_bus_routes_milestone_message(self):
        bus = MessageBus()
        bus.route({"from": "planner", "to": "coder", "type": "task", "data": {"goal": "Build API"}})
        message = bus.receive("coder")
        self.assertEqual(message.to_dict()["from"], "planner")
        self.assertEqual(message.data["goal"], "Build API")

    def test_message_bus_rejects_invalid_message(self):
        with self.assertRaises(ValueError):
            MessageBus().route({"from": "planner", "type": "task"})

    def test_queue_orders_tasks_and_tracks_statuses(self):
        queue = AgentTaskQueue()
        low = AgentTask("low", "planner", priority=1)
        high = AgentTask("high", "coder", priority=2)
        queue.enqueue(low)
        queue.enqueue(high)
        task = queue.dequeue()
        self.assertIs(task, high)
        self.assertEqual(task.status, "running")
        self.assertEqual(queue.complete(task, {"success": True}).status, "completed")

    def test_orchestrator_happy_path_uses_one_shared_context(self):
        agents = {name: FakeAgent({"success": True, "output": name}) for name in ("planner", "coder", "tester", "reviewer", "documentation")}
        result = AgentOrchestrator(registry_with(**agents)).run("Build API")
        self.assertTrue(result["success"])
        contexts = [agent.contexts[0] for agent in agents.values()]
        self.assertTrue(all(context is contexts[0] for context in contexts))

    def test_orchestrator_repairs_after_tester_failure(self):
        agents = {
            "planner": FakeAgent({"success": True, "output": "plan"}),
            "coder": FakeAgent({"success": True, "output": "created"}, {"success": True, "output": "repaired"}),
            "tester": FakeAgent({"success": False, "output": {"errors": ["bad"]}}, {"success": True, "output": "passed"}),
            "reviewer": FakeAgent({"success": True, "output": "approved"}),
            "documentation": FakeAgent({"success": True, "output": "docs"}),
        }
        result = AgentOrchestrator(registry_with(**agents)).run("Build API")
        self.assertTrue(result["success"])
        self.assertEqual(len(agents["coder"].contexts), 2)
        event_types = [event["type"] for event in result["context"].events]
        self.assertIn("VALIDATION_FAILED", event_types)
        self.assertIn("REPAIR_DONE", event_types)
        self.assertEqual(result["context"].events[-1]["type"], "PROJECT_FINISHED")

    def test_orchestrator_repairs_after_reviewer_failure(self):
        agents = {
            "planner": FakeAgent({"success": True, "output": "plan"}),
            "coder": FakeAgent({"success": True, "output": "created"}, {"success": True, "output": "repaired"}),
            "tester": FakeAgent({"success": True, "output": "passed"}, {"success": True, "output": "passed"}),
            "reviewer": FakeAgent({"success": False, "output": {"issues": ["naming"]}}, {"success": True, "output": "approved"}),
            "documentation": FakeAgent({"success": True, "output": "docs"}),
        }
        result = AgentOrchestrator(registry_with(**agents)).run("Build API")
        self.assertTrue(result["success"])
        self.assertEqual(len(agents["reviewer"].contexts), 2)

    def test_orchestrator_retries_the_planner(self):
        agents = {
            "planner": FakeAgent({"success": False, "output": "retry"}, {"success": True, "output": "plan"}),
            "coder": FakeAgent({"success": True, "output": "created"}),
            "tester": FakeAgent({"success": True, "output": "passed"}),
            "reviewer": FakeAgent({"success": True, "output": "approved"}),
            "documentation": FakeAgent({"success": True, "output": "docs"}),
        }
        self.assertTrue(AgentOrchestrator(registry_with(**agents)).run("Build API")["success"])
        self.assertEqual(len(agents["planner"].contexts), 2)

    def test_orchestrator_ignores_documentation_failure(self):
        agents = {name: FakeAgent({"success": True, "output": name}) for name in ("planner", "coder", "tester", "reviewer")}
        agents["documentation"] = FakeAgent({"success": False, "output": "disk full"})
        result = AgentOrchestrator(registry_with(**agents)).run("Build API")
        self.assertTrue(result["success"])
        self.assertEqual(result["context"].documentation_warning, "disk full")

    def test_orchestrator_reports_unknown_agent(self):
        result = AgentOrchestrator(AgentRegistry()).run("Build API")
        self.assertFalse(result["success"])
        self.assertEqual(result["failed_agent"], "planner")

    def test_orchestrator_preserves_dictionary_context(self):
        context = {"goal": "Build API", "memory": {"style": "clean"}}
        agents = {name: FakeAgent({"success": True, "output": name}) for name in ("planner", "coder", "tester", "reviewer", "documentation")}
        result = AgentOrchestrator(registry_with(**agents)).run(context=context)
        self.assertIs(result["context"], context)
        self.assertEqual(context["memory"]["style"], "clean")

    def test_orchestrator_generates_timeline_for_each_step(self):
        agents = {name: FakeAgent({"success": True, "output": name}) for name in ("planner", "coder", "tester", "reviewer", "documentation")}
        result = AgentOrchestrator(registry_with(**agents)).run("Build API")
        self.assertEqual([entry["agent"] for entry in result["timeline"]], list(("planner", "coder", "tester", "reviewer", "documentation")))
        self.assertTrue(all(entry["finished_at"] for entry in result["timeline"]))


if __name__ == "__main__":
    unittest.main()
