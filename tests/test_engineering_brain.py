import unittest

from app.engineering import EngineeringBrain, EngineeringDecisionReport


class TestEngineeringBrain(unittest.TestCase):
    def test_assessment_composes_quarter_one_decisions(self):
        report = EngineeringBrain().assess(
            "Build a hospital management system with authentication and payments"
        )

        self.assertIsInstance(report, EngineeringDecisionReport)
        payload = report.to_dict()
        self.assertEqual(payload["requirements"]["domain"], "hospital")
        self.assertTrue(payload["architecture"]["components"])
        self.assertTrue(payload["technology"]["backend"])
        self.assertTrue(payload["patterns"])
        self.assertTrue(payload["risks"]["risks"])
        self.assertGreater(payload["complexity"]["estimated_hours"], 0)
        self.assertIn("selected", payload["strategy"])
        self.assertTrue(payload["tradeoffs"])

    def test_rejects_empty_goal(self):
        with self.assertRaises(ValueError):
            EngineeringBrain().assess(" ")


if __name__ == "__main__":
    unittest.main()
