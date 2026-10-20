import unittest

from app.intelligence.strategy import BaseStrategy, StrategyManager, StrategyRegistry


class ResearchStrategy(BaseStrategy):
    name = "research"

    def matches(self, context):
        return bool(context.get("research"))

    def describe(self, context):
        return {"name": self.name, "description": "Research before implementation",
                "complexity": 0.5, "dependencies": 0.3, "estimated_minutes": 50}


class TestAdaptiveStrategy(unittest.TestCase):
    def test_custom_strategy_is_selected_from_context(self):
        manager = StrategyManager(registry=StrategyRegistry([ResearchStrategy()]))
        decision = manager.choose("Compare payment providers", {"research": True})
        self.assertEqual(decision.selected["name"], "research")

    def test_default_engine_remains_available(self):
        decision = StrategyManager().choose("Build a CRM")
        self.assertIn("selected", decision.to_dict())
        self.assertTrue(decision.alternatives)

    def test_registry_rejects_duplicates(self):
        registry = StrategyRegistry([ResearchStrategy()])
        with self.assertRaises(ValueError):
            registry.register(ResearchStrategy())


if __name__ == "__main__":
    unittest.main()
