import unittest

from app.reasoning.reasoning_engine import ReasoningEngine
from app.tools.tool_manager import ToolManager


class ReasoningEngineV1Tests(unittest.TestCase):
    def test_create_calculator_goal_completes_within_limit(self):
        engine = ReasoningEngine(tool_manager=ToolManager())

        result = engine.run("Create Calculator")

        self.assertIn("success", result)
        self.assertIn("iterations", result)
        self.assertIn("thoughts", result)
        self.assertIn("observations", result)
        self.assertLessEqual(result["iterations"], 10)

    def test_goal_selection_uses_search_for_project_analysis(self):
        engine = ReasoningEngine(tool_manager=ToolManager())

        result = engine.run("Analyze current project")

        self.assertTrue(result["thoughts"])
        self.assertEqual(result["thoughts"][0]["tool"], "search")

    def test_login_goal_triggers_search_then_finish(self):
        engine = ReasoningEngine(tool_manager=ToolManager())

        result = engine.run("Add login to existing project")

        self.assertTrue(result["thoughts"])
        self.assertIn(result["thoughts"][0]["tool"], {"search", "file"})

    def test_fix_runtime_error_goal_respects_iteration_limit(self):
        engine = ReasoningEngine(tool_manager=ToolManager())

        result = engine.run("Fix runtime error")

        self.assertIn("success", result)
        self.assertLessEqual(result["iterations"], 20)

    def test_search_for_authentication_code_reaches_search_tool(self):
        engine = ReasoningEngine(tool_manager=ToolManager())

        result = engine.run("Search for authentication code")

        self.assertTrue(result["thoughts"])
        self.assertEqual(result["thoughts"][0]["tool"], "search")

    def test_read_readme_reads_file(self):
        engine = ReasoningEngine(tool_manager=ToolManager())

        result = engine.run("Read README")

        self.assertTrue(result["thoughts"])
        self.assertEqual(result["thoughts"][0]["tool"], "file")
        self.assertEqual(result["thoughts"][0]["action"], "read")

    def test_valid_input_field_is_sent_to_tool_manager(self):
        class RecordingManager:
            def __init__(self):
                self.calls = []

            def execute(self, *args, **kwargs):
                self.calls.append((args, kwargs))
                return {"success": True, "output": "ok", "error": None}

        class ValidAI:
            def ask(self, prompt):
                return '{"thought":"read it","tool":"file","action":"read","input":"README.md","finished":true}'

        manager = RecordingManager()
        result = ReasoningEngine(tool_manager=manager, ai_manager=ValidAI()).run("Read README")

        self.assertTrue(result["success"])
        self.assertEqual(manager.calls[0][1]["path"], "README.md")

    def test_invalid_json_stops_with_observation(self):
        class InvalidAI:
            def ask(self, prompt):
                return "not json"

        result = ReasoningEngine(ai_manager=InvalidAI()).run("Inspect project")

        self.assertFalse(result["success"])
        self.assertEqual(result["iterations"], 1)
        self.assertFalse(result["observations"][0]["success"])

    def test_max_iteration_guard_stops_loop(self):
        class NeverFinishedAI:
            def ask(self, prompt):
                return '{"thought":"continue","tool":"search","action":"search","input":"x","finished":false}'

        result = ReasoningEngine(ai_manager=NeverFinishedAI(), max_iterations=3).run("Search x")

        self.assertFalse(result["success"])
        self.assertEqual(result["iterations"], 3)


if __name__ == "__main__":
    unittest.main()
