import unittest

from app.reasoning.reasoning_engine import ReasoningEngine
from app.tools.tool_manager import ToolManager


class ReasoningEngineTests(unittest.TestCase):
    def test_terminal_tool_blocks_dangerous_commands(self):
        manager = ToolManager()

        result = manager.execute("terminal", "run", command="rm -rf /tmp")

        self.assertFalse(result["success"])
        self.assertIn("Blocked", result["error"])

    def test_reasoning_engine_runs_a_tool_cycle(self):
        engine = ReasoningEngine(tool_manager=ToolManager())

        result = engine.run("Inspect the project for the ToolManager implementation")

        self.assertIn("status", result)
        self.assertIn("history", result)
        self.assertGreaterEqual(len(result["history"]), 1)


if __name__ == "__main__":
    unittest.main()
