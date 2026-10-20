import unittest

from app.engineering import DecisionIntelligenceEngine


class TestDecisionIntelligence(unittest.TestCase):
    def test_decision_contains_alternatives_estimates_and_safety_plans(self):
        package = DecisionIntelligenceEngine().decide(
            "Build a hospital management system with authentication and payments",
            constraints=["budget", "auditability"],
        )

        payload = package.to_dict()
        self.assertEqual(payload["constraints"], ["budget", "auditability"])
        self.assertGreaterEqual(len(payload["options"]), 3)
        self.assertIn("hours", payload["estimates"])
        self.assertTrue(payload["verification_plan"])
        self.assertTrue(payload["rollback_plan"])
        self.assertTrue(payload["learning_plan"])
        self.assertTrue(payload["risks"])

    def test_low_confidence_or_high_risk_routes_for_review(self):
        package = DecisionIntelligenceEngine().decide("Build an unclear production payment system")

        self.assertIn(package.route, {"ask_user", "critic", "reflect"})
        self.assertLess(package.confidence, 0.8)

    def test_rejects_empty_goal(self):
        with self.assertRaises(ValueError):
            DecisionIntelligenceEngine().decide(" ")


if __name__ == "__main__":
    unittest.main()
