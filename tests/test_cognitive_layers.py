import unittest

from app.diagnostics.health_checker import HealthChecker
from app.events.event_bus import EventBus
from app.events.event_types import ACTION_FINISHED
from app.metrics.metrics_manager import MetricsManager
from app.reasoning.action import Action
from app.reasoning.action_executor import ActionExecutor
from app.reasoning.memory_summarizer import MemorySummarizer
from app.reasoning.observation import Observation


class FakeTools:
    def execute(self, *args, **kwargs):
        return {"success": True, "output": "ok", "error": None}

    def names(self):
        return ["file"]


class CognitiveLayerTests(unittest.TestCase):
    def test_action_executor_returns_observation_and_events(self):
        bus = EventBus()
        executor = ActionExecutor(FakeTools(), event_bus=bus)

        result = executor.execute(Action("file", "read", {"path": "README.md"}))

        self.assertIsInstance(result, Observation)
        self.assertEqual(result["success"], True)
        self.assertEqual(bus.history[-1].event_type, ACTION_FINISHED)

    def test_metrics_export_tracks_runtime_and_success_rate(self):
        metrics = MetricsManager()
        metrics.record("tool_calls")
        metrics.record("failures")
        metrics.record_runtime(0.5)

        report = metrics.export()

        self.assertEqual(report["tool_calls"], 1)
        self.assertEqual(report["average_runtime"], 0.5)
        self.assertEqual(report["success_rate"], 0.0)

    def test_summarizer_keeps_recent_history(self):
        history = [{"action": {"action": str(index)}} for index in range(12)]

        result = MemorySummarizer(interval=10).summarize(history)

        self.assertEqual(len(result["history"]), 10)
        self.assertIn("recent actions", result["summary"])

    def test_health_checker_reports_tool_and_event_bus(self):
        result = HealthChecker(tools=FakeTools(), event_bus=EventBus()).check()

        self.assertTrue(result["checks"]["tools"])
        self.assertTrue(result["checks"]["event_bus"])


if __name__ == "__main__":
    unittest.main()