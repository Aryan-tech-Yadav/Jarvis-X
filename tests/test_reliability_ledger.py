import tempfile
import unittest

from app.benchmark import ReliabilityLedger, ReliabilityRun, classify_failure


class TestReliabilityLedger(unittest.TestCase):
    def test_classifies_observable_failures(self):
        self.assertEqual(classify_failure("request timed out"), "timeout")
        self.assertEqual(classify_failure("schema validation failed"), "validation")
        self.assertEqual(classify_failure("worker exception"), "crash")
        self.assertEqual(classify_failure(recovered=True), "recovery")
        self.assertEqual(classify_failure(manual_intervention=0.2), "intervention")

    def test_persists_runs_and_summarizes_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            path = f"{directory}/reliability.json"
            ledger = ReliabilityLedger(path)
            ledger.record(ReliabilityRun("hospital", True))
            ledger.record({
                "benchmark_id": "hospital",
                "success": False,
                "recovered": True,
                "error": "worker crashed",
            })

            restored = ReliabilityLedger(path)
            summary = restored.summary()
            self.assertEqual(summary["total_runs"], 2)
            self.assertEqual(summary["successful_runs"], 1)
            self.assertEqual(summary["recovery_rate"], 0.5)
            self.assertEqual(summary["failure_classes"], {"recovery": 1})

    def test_rejects_unknown_failure_class(self):
        with self.assertRaises(ValueError):
            ReliabilityLedger().record({
                "benchmark_id": "todo-app",
                "failure_class": "made-up",
            })


if __name__ == "__main__":
    unittest.main()
