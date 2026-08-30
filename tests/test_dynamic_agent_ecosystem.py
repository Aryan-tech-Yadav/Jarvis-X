import unittest

from app.agents.dynamic_loader import AgentLoader
from app.agents.lifecycle import AgentLifecycleManager
from app.agents.sandbox import AgentSandbox


class DemoAgent:
    name = "demo"
    version = "2.0"
    capabilities = ("testing",)
    priority = 4
    dependencies = ("python",)
    permissions = ("read",)

    def __init__(self):
        self.initialized = False
        self.stopped = False

    def initialize(self):
        self.initialized = True
        return True

    def shutdown(self):
        self.stopped = True
        return True

    def execute(self, task):
        return {"success": True, "output": task}

    def health_check(self):
        return self.initialized and not self.stopped


class TestDynamicAgentEcosystem(unittest.TestCase):
    def test_loader_loads_agent_class(self):
        loaded = AgentLoader().load_class(__name__, "DemoAgent")
        self.assertIs(loaded, DemoAgent)

    def test_lifecycle_spawn_and_unload(self):
        manager = AgentLifecycleManager()
        agent = manager.spawn(DemoAgent())
        self.assertEqual(manager.find_by_capability("testing"), [agent])
        self.assertEqual(manager.unload("demo"), agent)
        self.assertIsNone(manager.registry.get("demo"))

    def test_metadata_exposes_operational_details(self):
        manager = AgentLifecycleManager()
        manager.spawn(DemoAgent())
        metadata = manager.metadata()[0]
        self.assertEqual(metadata["version"], "2.0")
        self.assertEqual(metadata["priority"], 4)
        self.assertEqual(metadata["health"], "healthy")

    def test_sandbox_rejects_path_escape(self):
        sandbox = AgentSandbox("workspace")
        self.assertTrue(sandbox.contains("project/file.py"))
        self.assertFalse(sandbox.contains("../outside.py"))


if __name__ == "__main__":
    unittest.main()
