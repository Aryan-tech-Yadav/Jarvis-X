import unittest

from app.quality import LifecycleQualityGate, REQUIRED_STAGES


class TestLifecycleQualityGate(unittest.TestCase):
    def _evidence(self, **overrides):
        evidence = {stage: {"passed": True} for stage in REQUIRED_STAGES}
        evidence.update(overrides)
        return evidence

    def test_approves_only_when_all_lifecycle_stages_have_evidence(self):
        result = LifecycleQualityGate().evaluate(self._evidence())

        self.assertTrue(result.passed)
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.blockers, ())
        self.assertEqual(len(result.to_dict()["stages"]), len(REQUIRED_STAGES))

    def test_missing_and_failed_stages_are_explicit_blockers(self):
        evidence = self._evidence(security_scan={"passed": False, "reason": "Secrets found"})
        del evidence["reflection"]

        result = LifecycleQualityGate().evaluate(evidence)

        self.assertFalse(result.passed)
        self.assertEqual(result.score, 0.7778)
        self.assertIn("Secrets found", result.blockers)
        self.assertIn("reflection evidence is missing", result.blockers)

    def test_rejects_invalid_evidence(self):
        with self.assertRaises(TypeError):
            LifecycleQualityGate().evaluate([])


if __name__ == "__main__":
    unittest.main()
