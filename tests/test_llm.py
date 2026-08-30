import unittest

from app.ai.ai_manager import AIManager
from app.llm.cost_tracker import CostTracker
from app.llm.latency_tracker import LatencyTracker
from app.llm.llm_router import LLMRouter
from app.llm.model_selector import ModelSelector


class FakeProvider:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def complete(self, prompt, model=None, **kwargs):
        self.calls.append((prompt, model, kwargs))
        if self.error:
            raise self.error
        return self.response


class FakeRouter:
    def __init__(self):
        self.calls = []

    def ask(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        return "answer"


class LLMTests(unittest.TestCase):
    def test_router_falls_back_and_records_metrics(self):
        failing = FakeProvider(error=RuntimeError("offline"))
        working = FakeProvider(response="fallback")
        cost = CostTracker()
        latency = LatencyTracker()
        router = LLMRouter(
            providers={"first": failing, "second": working},
            cost_tracker=cost,
            latency_tracker=latency,
        )

        result = router.ask("hello", provider=None, cost=0.25)

        self.assertEqual(result, "fallback")
        self.assertEqual(len(failing.calls), 1)
        self.assertEqual(len(working.calls), 1)
        self.assertEqual(cost.total, 0.25)
        self.assertIsNotNone(latency.average("second"))

    def test_selector_prefers_coding_quality_then_cost(self):
        selector = ModelSelector({
            "cheap": {"coding": 5, "cost": 1, "latency": 1},
            "coder": {"coding": 9, "cost": 4, "latency": 2},
        })

        self.assertEqual(selector.select("coding"), "coder")

    def test_ai_manager_preserves_public_api_and_messages(self):
        router = FakeRouter()
        manager = AIManager(router=router)

        result = manager.ask("hello")

        self.assertEqual(result, "answer")
        self.assertEqual(len(router.calls[0][1]["messages"]), 3)
        self.assertEqual(manager.chat.get_messages()[-1]["content"], "answer")


if __name__ == "__main__":
    unittest.main()