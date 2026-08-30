"""Integration test for Sprint 10 tool ecosystem.

Tests:
  - Dynamic tool discovery
  - Registry auto-population via loader
  - Tool chaining
  - Permission-aware execution
  - Capability-based selection
"""

import os
import tempfile
import unittest

from app.tools.loader import ToolLoader
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_selector import ToolSelector
from app.tools.permission_manager import PermissionManager
from app.tools.tool_chain import ToolChain
from app.tools.filesystem import FileSystemTool
from app.tools.git import GitTool
from app.tools.docker import DockerTool
from app.tools.terminal_tool import TerminalTool
from app.tools.memory import MemoryTool
from app.tools.automation import AutomationTool


class TestToolEcosystemIntegration(unittest.TestCase):
    def test_dynamic_discovery_loads_all_builtin_tools(self):
        loader = ToolLoader(tools_root="app/tools")
        modules = loader.discover()
        loaded = loader.load_all(modules)
        names = [l.tool.metadata.name for l in loaded]
        self.assertIn("git", names)
        self.assertIn("docker", names)
        self.assertIn("filesystem", names)
        self.assertIn("browser", names)
        self.assertIn("internet", names)
        self.assertIn("memory", names)
        self.assertIn("database", names)
        self.assertIn("vscode", names)
        self.assertIn("automation", names)

    def test_registry_populated_via_loader(self):
        loader = ToolLoader(tools_root="app/tools")
        loaded = loader.load_all()
        registry = ToolRegistry()
        for entry in loaded:
            registry.register(entry.tool)
        self.assertGreaterEqual(len(registry.names()), 10)

    def test_capability_based_selection(self):
        registry = ToolRegistry()
        registry.register(GitTool())
        registry.register(DockerTool())
        registry.register(FileSystemTool())

        selector = ToolSelector(registry=registry)

        git_tool = selector.select("version control")
        self.assertIsNotNone(git_tool)
        self.assertEqual(git_tool.metadata.name, "git")

        docker_tool = selector.select("container")
        self.assertIsNotNone(docker_tool)
        self.assertEqual(docker_tool.metadata.name, "docker")

        fs_tool = selector.select("file system")
        self.assertIsNotNone(fs_tool)
        self.assertEqual(fs_tool.metadata.name, "filesystem")

    def test_tool_chain_executes_sequence(self):
        registry = ToolRegistry()
        registry.register(FileSystemTool())
        registry.register(MemoryTool())
        registry.register(AutomationTool())

        chain = ToolChain(registry=registry)
        chain.add("filesystem", "list", params={"path": "."})
        chain.add("memory", "remember", params={"key": "chain_test", "value": "success"})
        chain.add("automation", "notify", params={"message": "Chain completed"})

        result = chain.execute_all(registry)
        self.assertTrue(result.success)
        self.assertEqual(result.steps_executed, 3)

    def test_permission_blocks_dangerous_tool(self):
        registry = ToolRegistry()
        pm = PermissionManager(auto_approve=False)
        registry._permission_manager = pm

        tool = TerminalTool()
        registry.register(tool)

        # Safe command should work
        result = registry.execute("terminal", "run", context={"command": "echo hello"})
        self.assertTrue(result.get("success", False) or "Blocked" not in result.get("error", ""))

        # Dangerous command should be blocked
        result = registry.execute("terminal", "run", context={"command": "rm -rf /"})
        self.assertFalse(result.get("success", True))
        self.assertIn("Blocked", result.get("error", ""))

    def test_tool_executor_dispatches_without_if_else(self):
        registry = ToolRegistry()
        registry.register(GitTool())
        registry.register(DockerTool())
        registry.register(FileSystemTool())

        executor = ToolExecutor(registry=registry)

        # These should all work via registry dispatch, not hardcoded if-else
        result = executor.execute("git", action="status")
        self.assertIn("success", result)

        result = executor.execute("docker", action="ps")
        self.assertIn("success", result)

        result = executor.execute("filesystem", action="list", context={"path": "."})
        self.assertTrue(result.get("success", False))

    def test_loader_dynamic_plugin_dropin(self):
        """Test that the loader can find and load tools from the real tools directory."""
        loader = ToolLoader(tools_root="app/tools")
        modules = loader.discover()
        # Should discover all built-in tools
        self.assertGreaterEqual(len(modules), 10)
        module_names = [m.split(".")[-1] for m in modules]
        self.assertIn("git", module_names)
        self.assertIn("docker", module_names)
        self.assertIn("filesystem", module_names)

        # Load all discovered tools
        loaded = loader.load_all(modules)
        names = [l.tool.metadata.name for l in loaded]
        self.assertIn("git", names)
        self.assertIn("docker", names)
        self.assertIn("filesystem", names)


if __name__ == "__main__":
    unittest.main()
