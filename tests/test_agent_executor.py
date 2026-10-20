import unittest

from app.agent.agent_executor import AgentExecutor
from app.reasoning.reasoning_engine import ReasoningEngine


class RecordingToolManager:
    def __init__(self, results=None):
        self.calls = []
        self.results = list(results or [{"success": True, "output": "ok", "error": None}])

    def execute(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.results.pop(0) if self.results else {"success": True, "output": "ok", "error": None}


class SequenceAI:
    def __init__(self, responses):
        self.responses = iter(responses)

    def ask(self, prompt):
        return next(self.responses)


class AgentExecutorTests(unittest.TestCase):
    def test_finish_stops_immediately_and_keeps_history(self):
        manager = RecordingToolManager()
        ai = SequenceAI(['{"thought":"read","tool":"file","action":"read","input":"README.md","finish":true}'])

        result = AgentExecutor(ai_manager=ai, tool_manager=manager).run("Read README")

        self.assertTrue(result["success"])
        self.assertEqual(result["iterations"], 1)
        self.assertEqual(len(result["actions"]), 1)
        self.assertEqual(len(result["observations"]), 1)
        self.assertEqual(manager.calls[0][1]["path"], "README.md")

    def test_tool_error_is_fed_back_for_recovery(self):
        manager = RecordingToolManager([
            {"success": False, "output": "", "error": "missing file"},
            {"success": True, "output": "fixed", "error": None},
        ])
        ai = SequenceAI([
            '{"thought":"read","tool":"file","action":"read","input":"missing.py","finish":false}',
            '{"thought":"use README","tool":"file","action":"read","input":"README.md","finish":true}',
        ])

        result = AgentExecutor(ai_manager=ai, tool_manager=manager).run("Read project file")

        self.assertTrue(result["success"])
        self.assertEqual(result["iterations"], 2)
        self.assertEqual(len(result["observations"]), 2)

    def test_unknown_tool_fails_without_direct_tool_execution(self):
        ai = SequenceAI(['{"thought":"bad","tool":"teleport","action":"run","input":{},"finish":false}'])

        result = AgentExecutor(ai_manager=ai).run("Do something")

        self.assertFalse(result["success"])
        self.assertIn("Unknown tool", result["result"])
        self.assertEqual(result["iterations"], 1)

    def test_max_iterations_is_enforced(self):
        ai = SequenceAI(['{"thought":"continue","tool":"search","action":"search","input":"x","finish":false}'] * 3)

        result = AgentExecutor(ai_manager=ai, max_iterations=3).run("Search x")

        self.assertFalse(result["success"])
        self.assertEqual(result["iterations"], 3)

    def test_invalid_json_is_reported_as_observation(self):
        ai = SequenceAI(["Hello sir..."])

        result = AgentExecutor(ai_manager=ai).run("Inspect project")

        self.assertFalse(result["success"])
        self.assertEqual(result["iterations"], 1)
        self.assertFalse(result["observations"][0]["success"])


if __name__ == "__main__":
    unittest.main()