"""Tests for Sprint 10 tool ecosystem."""

import os
import tempfile
import unittest

from app.tools.base_tool import BaseTool, ToolMetadata, ToolResult
from app.tools.tool_registry import ToolRegistry
from app.tools.tool_executor import ToolExecutor
from app.tools.tool_selector import ToolSelector
from app.tools.tool_cache import ToolCache
from app.tools.tool_ranker import ToolRanker
from app.tools.tool_history import ToolHistory, ToolCall
from app.tools.loader import ToolLoader, LoadedTool
from app.tools.permission_manager import PermissionManager, PermissionRule, PermissionResult
from app.tools.tool_chain import ToolChain, ChainStep, ChainResult
from app.tools.filesystem import FileSystemTool
from app.tools.git import GitTool
from app.tools.docker import DockerTool
from app.tools.browser import BrowserTool
from app.tools.internet import InternetTool
from app.tools.memory import MemoryTool
from app.tools.database import DatabaseTool
from app.tools.vscode import VSCodeTool
from app.tools.automation import AutomationTool
from app.tools.file_tool import FileTool
from app.tools.python_tool import PythonTool
from app.tools.terminal_tool import TerminalTool
from app.tools.search_tool import SearchTool


class TestBaseTool(unittest.TestCase):
    def test_metadata_defaults(self):
        tool = BaseTool()
        self.assertEqual(tool.metadata.name, "BaseTool")
        self.assertEqual(tool.metadata.version, "1.0.0")
        self.assertTrue(tool.metadata.enabled)

    def test_tool_result_ok(self):
        result = ToolResult.ok(output="hello")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "hello")
        self.assertIsNone(result.error)

    def test_tool_result_fail(self):
        result = ToolResult.fail("something went wrong")
        self.assertFalse(result.success)
        self.assertEqual(result.error, "something went wrong")

    def test_tool_result_to_dict(self):
        result = ToolResult.ok("data", artifacts=["f1"], duration=1.5)
        data = result.to_dict()
        self.assertEqual(data["success"], True)
        self.assertEqual(data["output"], "data")
        self.assertIn("f1", data["artifacts"])
        self.assertAlmostEqual(data["duration"], 1.5)


class TestToolRegistry(unittest.TestCase):
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = FileSystemTool()
        name = registry.register(tool)
        self.assertEqual(name, "filesystem")
        retrieved = registry.get("filesystem")
        self.assertIs(retrieved, tool)

    def test_register_duplicate_raises(self):
        registry = ToolRegistry()
        registry.register(FileSystemTool())
        with self.assertRaises(ValueError):
            registry.register(FileSystemTool())

    def test_register_non_tool_raises(self):
        registry = ToolRegistry()
        with self.assertRaises(TypeError):
            registry.register("not a tool")

    def test_execute_success(self):
        registry = ToolRegistry()
        registry.register(FileSystemTool())
        result = registry.execute("filesystem", "list", context={"path": "."})
        self.assertTrue(result.get("success", False))

    def test_execute_unknown_tool(self):
        registry = ToolRegistry()
        result = registry.execute("nonexistent", "action")
        self.assertFalse(result["success"])
        self.assertIn("not registered", result["error"])

    def test_search(self):
        registry = ToolRegistry()
        registry.register(GitTool())
        registry.register(DockerTool())
        results = registry.search("git")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metadata.name, "git")

    def test_find_by_action(self):
        registry = ToolRegistry()
        registry.register(GitTool())
        tools = registry.find_by_action("clone")
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0].metadata.name, "git")

    def test_metadata(self):
        registry = ToolRegistry()
        registry.register(GitTool())
        meta = registry.metadata()
        self.assertEqual(len(meta), 1)
        self.assertEqual(meta[0]["name"], "git")


class TestToolExecutor(unittest.TestCase):
    def test_execute_via_registry(self):
        registry = ToolRegistry()
        registry.register(FileSystemTool())
        executor = ToolExecutor(registry=registry)
        result = executor.execute("filesystem", action="list", context={"path": "."})
        self.assertTrue(result.get("success", False))

    def test_execute_unknown_without_registry(self):
        executor = ToolExecutor(registry=None)
        result = executor.execute("unknown", "action")
        self.assertFalse(result["success"])


class TestToolSelector(unittest.TestCase):
    def test_select_by_capability(self):
        registry = ToolRegistry()
        registry.register(GitTool())
        registry.register(DockerTool())
        selector = ToolSelector(registry=registry)
        tool = selector.select("version control")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.metadata.name, "git")

    def test_select_by_action(self):
        registry = ToolRegistry()
        registry.register(GitTool())
        registry.register(DockerTool())
        selector = ToolSelector(registry=registry)
        tool = selector.select("docker", action="run")
        self.assertIsNotNone(tool)
        self.assertEqual(tool.metadata.name, "docker")

    def test_select_no_match(self):
        registry = ToolRegistry()
        selector = ToolSelector(registry=registry)
        tool = selector.select("nonexistent capability")
        self.assertIsNone(tool)


class TestToolCache(unittest.TestCase):
    def test_set_and_get(self):
        cache = ToolCache(default_ttl=60)
        cache.set("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

    def test_expired(self):
        cache = ToolCache(default_ttl=0)
        cache.set("key1", "value1")
        self.assertIsNone(cache.get("key1"))

    def test_clear(self):
        cache = ToolCache()
        cache.set("key1", "value1")
        cache.clear()
        self.assertIsNone(cache.get("key1"))


class TestToolRanker(unittest.TestCase):
    def test_score_matches_name(self):
        ranker = ToolRanker()
        tool = {"name": "git", "description": "Git operations", "priority": 10}
        score = ranker.score(tool, "git clone")
        self.assertGreater(score, 0)

    def test_rank_sorts_descending(self):
        ranker = ToolRanker()
        tools = [
            {"name": "docker", "description": "Docker", "priority": 0},
            {"name": "git", "description": "Git", "priority": 10},
        ]
        ranked = ranker.rank(tools, "git")
        self.assertEqual(ranked[0]["name"], "git")


class TestToolHistory(unittest.TestCase):
    def test_record_and_list(self):
        history = ToolHistory()
        history.record(ToolCall("git", 1.0, True))
        history.record(ToolCall("docker", 2.0, False, failure="timeout"))
        calls = history.list()
        self.assertEqual(len(calls), 2)

    def test_statistics(self):
        history = ToolHistory()
        history.record(ToolCall("git", 1.0, True))
        history.record(ToolCall("git", 0.5, True))
        stats = history.statistics()
        self.assertEqual(stats["git"]["calls"], 2)
        self.assertEqual(stats["git"]["success_rate"], 1.0)


class TestPermissionManager(unittest.TestCase):
    def test_safe_permission_allowed(self):
        pm = PermissionManager(auto_approve=False)
        result = pm.check("filesystem", "read", ["filesystem.read"])
        self.assertTrue(result.allowed)

    def test_dangerous_permission_denied(self):
        pm = PermissionManager(auto_approve=False)
        result = pm.check("terminal", "exec", ["terminal.sudo"])
        self.assertFalse(result.allowed)
        self.assertTrue(result.requires_approval)

    def test_auto_approve(self):
        pm = PermissionManager(auto_approve=True)
        result = pm.check("terminal", "exec", ["terminal.sudo"])
        self.assertTrue(result.allowed)

    def test_callback_approval(self):
        approved = []
        def callback(tool, action, perms):
            approved.append((tool, action))
            return True
        pm = PermissionManager(auto_approve=False)
        pm.add_approval_callback(callback)
        result = pm.check("terminal", "exec", ["terminal.sudo"])
        self.assertTrue(result.allowed)
        self.assertEqual(len(approved), 1)


class TestToolChain(unittest.TestCase):
    def test_chain_execution(self):
        registry = ToolRegistry()
        registry.register(FileSystemTool())
        chain = ToolChain(registry=registry)
        chain.add("filesystem", "list", params={"path": "."})
        result = chain.execute_all(registry)
        self.assertTrue(result.success)
        self.assertEqual(result.steps_executed, 1)

    def test_chain_on_failure_stop(self):
        registry = ToolRegistry()
        registry.register(FileSystemTool())
        chain = ToolChain(registry=registry)
        chain.add("filesystem", "list", params={"path": "."})
        chain.add("nonexistent", "action", on_failure="stop")
        result = chain.execute_all(registry)
        self.assertFalse(result.success)
        self.assertEqual(result.steps_executed, 1)

    def test_chain_steps(self):
        chain = ToolChain()
        chain.add("git", "clone", params={"repo": "https://github.com/test/test"})
        chain.add("python", "run", params={"file_name": "main.py"})
        steps = chain.steps()
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0]["tool_name"], "git")


class TestBuiltinTools(unittest.TestCase):
    def test_filesystem_read_write(self):
        tool = FileSystemTool()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            result = tool.run("write", path=path, content="hello")
            self.assertTrue(result["success"])
            read_result = tool.run("read", path=path)
            self.assertTrue(read_result["success"])
            self.assertEqual(read_result["output"], "hello")
        finally:
            os.remove(path)

    def test_git_actions(self):
        tool = GitTool()
        actions = ["status", "log", "branch", "init"]
        for action in actions:
            result = tool.run(action)
            self.assertIn("success", result)

    def test_docker_ps(self):
        tool = DockerTool()
        result = tool.run("ps")
        self.assertIn("success", result)

    def test_browser_open(self):
        tool = BrowserTool()
        # Mock the internal _open_browser to avoid actually opening a browser
        original_open = tool._open_browser
        tool._open_browser = lambda url, **kwargs: ToolResult.ok(output=f"Opened: {url}").to_dict()
        try:
            result = tool.run("open", url="https://example.com")
            self.assertTrue(result["success"])
        finally:
            tool._open_browser = original_open

    def test_internet_search(self):
        tool = InternetTool()
        result = tool.run("search", query="python")
        # Internet search may fail in test environment, but should not crash
        self.assertIn("success", result)

    def test_memory_remember_recall(self):
        tool = MemoryTool()
        tool.run("remember", key="test", value="value")
        result = tool.run("recall", key="test")
        self.assertTrue(result["success"])
        self.assertEqual(result["output"], "value")

    def test_database_operations(self):
        tool = DatabaseTool()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            # Close the temp file so SQLite can use it
            f.close()
            result = tool.run("create_table", path=db_path, table="users",
                              schema="id INTEGER PRIMARY KEY, name TEXT")
            self.assertTrue(result["success"])
            result = tool.run("list_tables", path=db_path)
            self.assertTrue(result["success"])
            self.assertIn("users", result["output"])
            result = tool.run("insert", path=db_path, table="users", data={"name": "Alice"})
            self.assertTrue(result["success"])
            # Query back the data
            result = tool.run("query", path=db_path, query="SELECT * FROM users")
            self.assertTrue(result["success"])
            self.assertIsInstance(result["output"], dict)
        finally:
            try:
                os.remove(db_path)
            except OSError:
                pass

    def test_vscode_actions(self):
        tool = VSCodeTool()
        result = tool.run("list_files", path=".")
        self.assertTrue(result["success"])

    def test_automation_notify(self):
        tool = AutomationTool()
        result = tool.run("notify", message="Hello from Jarvis")
        self.assertTrue(result["success"])

    def test_legacy_file_tool(self):
        tool = FileTool()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            result = tool.run("write", path=path, content="legacy")
            self.assertTrue(result["success"])
        finally:
            os.remove(path)

    def test_python_tool_run(self):
        tool = PythonTool()
        result = tool.run("exec", code="print('hello')")
        self.assertTrue(result["success"])
        self.assertIn("hello", result.get("output", ""))

    def test_terminal_tool_forbidden(self):
        tool = TerminalTool()
        result = tool.run("exec", command="rm -rf /")
        self.assertFalse(result["success"])
        self.assertIn("Blocked", result["error"])


class TestToolDiscovery(unittest.TestCase):
    def test_loader_discover_modules(self):
        loader = ToolLoader(tools_root="app/tools")
        modules = loader.discover()
        self.assertIsInstance(modules, list)
        self.assertIn("app.tools.git", modules)

    def test_loader_load_git(self):
        loader = ToolLoader(tools_root="app/tools")
        loaded = loader.load("app.tools.git", "GitTool")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.tool.metadata.name, "git")

    def test_loader_load_all(self):
        loader = ToolLoader(tools_root="app/tools")
        loaded = loader.load_all()
        names = [l.metadata.name for l in loaded]
        self.assertIn("git", names)
        self.assertIn("docker", names)
        self.assertIn("filesystem", names)
        self.assertIn("vscode", names)
