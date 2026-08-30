import unittest

from app.evaluation import SelfImprovementCore


class TestSelfImprovementCore(unittest.TestCase):
    def test_cycle_observes_critiques_and_generates_three_proposals(self):
        sic = SelfImprovementCore()
        observation = sic.observe(
            "planner-run-1",
            outcome="failed",
            metrics={"confidence": 0.95, "assumptions": ["environment is ready"]},
            failures=["ModuleNotFoundError: No module named 'x'"],
        )

        report = sic.cycle(observation)

        self.assertEqual(len(report.proposals), 3)
        self.assertTrue(report.critique["overconfident"])
        self.assertEqual(report.proposals[2]["diagnosis"]["diagnosis"]["error_category"], "import")
        self.assertEqual(report.decision, "defer")

    def test_sic_never_experiments_without_an_injected_builder(self):
        sic = SelfImprovementCore()
        observation = sic.observe("safe-task", outcome="success")

        report = sic.cycle(observation, opportunities=[{"id": "candidate"}])

        self.assertFalse(report.experiment["executed"])
        self.assertIn("builder", report.experiment["reason"])


if __name__ == "__main__":
    unittest.main()
