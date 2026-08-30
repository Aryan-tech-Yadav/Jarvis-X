import os
import tempfile
import unittest

from app.tools.tool_manager import ToolManager


class ToolManagerTests(unittest.TestCase):
    def test_file_tool_read_and_write(self):
        manager = ToolManager()

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "demo.txt")

            write_result = manager.execute("file", "write", path=file_path, content="hello tool")
            self.assertTrue(write_result["success"], write_result)

            read_result = manager.execute("file", "read", path=file_path)
            self.assertTrue(read_result["success"], read_result)
            self.assertEqual(read_result["output"], "hello tool")

    def test_terminal_tool_runs_command(self):
        manager = ToolManager()

        result = manager.execute("terminal", "run", command="python --version")

        self.assertTrue(result["success"], result)
        self.assertIn("Python", result["output"])

    def test_unknown_tool_is_handled_cleanly(self):
        manager = ToolManager()

        result = manager.execute("unknown_tool", "read")

        self.assertFalse(result["success"])
        self.assertIn("Unknown tool", result["error"])

    def test_invalid_action_is_handled_cleanly(self):
        manager = ToolManager()

        result = manager.execute("file", "explode")

        self.assertFalse(result["success"])
        self.assertIn("Unsupported action", result["error"])


if __name__ == "__main__":
    unittest.main()
