import unittest

from app.intelligence import MetaEngineeringEngine


class TestMetaEngineering(unittest.TestCase):
    def test_uncertainty_routes_ambiguous_work_to_user(self):
        result = MetaEngineeringEngine().assess_uncertainty({
            "known_facts": ["project type"],
            "unknowns": ["deadline", "deployment"],
            "assumptions": ["PostgreSQL"],
            "risk_score": 20,
        })

        self.assertEqual(result.action, "ask_user")
        self.assertLess(result.confidence, 0.8)

    def test_meta_review_detects_overconfidence_and_repeated_mistake(self):
        result = MetaEngineeringEngine().review_thinking({
            "goal": "deploy service",
            "assumptions": ["environment is configured"],
            "risks": ["migration"],
            "alternatives": ["staged rollout"],
            "confidence": 0.95,
            "repeated_mistake": True,
        })

        self.assertTrue(result.overconfident)
        self.assertTrue(result.repeated_mistake)
        self.assertTrue(result.reasons)

    def test_debugger_returns_a_gated_proposal_without_mutating_code(self):
        result = MetaEngineeringEngine().propose_debug_repair(
            "ModuleNotFoundError: No module named 'missing_pkg'"
        )

        self.assertEqual(result.kind, "debug_repair")
        self.assertEqual(result.diagnosis["error_category"], "import")
        self.assertTrue(result.verification)
        self.assertIn("requires_approval", result.to_dict())


if __name__ == "__main__":
    unittest.main()
