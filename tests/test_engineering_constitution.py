import unittest

from app.intelligence import ConfidenceEngine, EngineeringConstitution


class TestEngineeringConstitution(unittest.TestCase):
    def test_low_confidence_and_known_mistake_block_automatic_decision(self):
        constitution = EngineeringConstitution()
        result = constitution.validate(
            {"action": "deploy"},
            confidence=0.65,
            evidence={"known_mistake": True, "quality_gate_passed": True},
        )

        self.assertFalse(result.approved)
        self.assertIn("P007", result.principles)
        self.assertIn("P002", result.principles)

    def test_secrets_and_quality_gate_are_hard_blockers(self):
        result = EngineeringConstitution().validate(
            {"action": "release"},
            confidence=0.99,
            evidence={"secrets_detected": True, "quality_gate_passed": False},
        )

        self.assertFalse(result.approved)
        self.assertEqual(set(result.principles), {"P003", "P006"})

    def test_confidence_engine_is_bounded_and_routes_low_confidence_to_user(self):
        engine = ConfidenceEngine()
        confidence = engine.evaluate({
            "base": 0.7,
            "validated_facts": ["architecture"],
            "uncertainties": ["deployment", "cost"],
            "high_risk": True,
        })

        self.assertEqual(confidence, 0.4)
        self.assertEqual(engine.route(confidence), "ask_user")


if __name__ == "__main__":
    unittest.main()
