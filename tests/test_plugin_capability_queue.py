import tempfile
import unittest
from types import SimpleNamespace

from app.capabilities.capability import Capability
from app.capabilities.capability_matcher import CapabilityMatcher
from app.capabilities.capability_registry import CapabilityRegistry
from app.plugins.plugin import Plugin
from app.plugins.plugin_manager import PluginManager
from app.tasks.task_queue import TaskQueue
from app.tasks.task_worker import TaskWorker


class ExamplePlugin(Plugin):
    name = "example"


class PluginCapabilityQueueTests(unittest.TestCase):
    def test_plugin_lifecycle_and_duplicate_detection(self):
        manager = PluginManager()
        plugin = ExamplePlugin()

        manager.register(plugin)

        self.assertIs(manager.get("example"), plugin)
        with self.assertRaises(ValueError):
            manager.register(plugin)
        self.assertIs(manager.unregister("example"), plugin)

    def test_capability_matcher_prefers_priority(self):
        registry = CapabilityRegistry()
        registry.register(Capability("search", "find files", object(), priority=1))
        registry.register(Capability("search-fast", "fast file search", object(), priority=5))

        self.assertEqual(CapabilityMatcher(registry).best("search").name, "search-fast")

    def test_queue_worker_lifecycle_and_cancel(self):
        queue = TaskQueue()
        first = SimpleNamespace(result=None)
        second = SimpleNamespace(result=None)
        first_id = queue.submit(first)
        second_id = queue.submit(second)
        self.assertTrue(queue.cancel(second_id))

        result = TaskWorker(queue, lambda task: {"task": task.task_id}).run_once()

        self.assertEqual(result["task"], first_id)
        self.assertEqual(queue.status(first_id), "completed")
        self.assertEqual(queue.status(second_id), "cancelled")
        self.assertEqual(len(queue.history()), 2)


if __name__ == "__main__":
    unittest.main()