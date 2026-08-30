import unittest

from app.evaluation import EngineeringMaturityEngine


class TestEngineeringMaturity(unittest.TestCase):
    def test_scores_maturity_and_tracks_weakest_skill(self):
        engine = EngineeringMaturityEngine()
        result = engine.score({
            "requirement_understanding": 96,
            "planning": 91,
            "architecture": 95,
            "code_quality": 98,
            "security": 94,
            "performance": 88,
            "maintainability": 97,
            "testing": 92,
            "debugging": 81,
            "research": 90,
            "optimization": 72,
        })

        self.assertEqual(result.level, "EML-5")
        self.assertEqual(result.weakest_skill, "optimization")
        self.assertEqual(engine.skill_graph()["weakest_skill"], "optimization")
        self.assertEqual(len(engine.timeline()), 1)

    def test_governance_blocks_unverified_change(self):
        result = EngineeringMaturityEngine.govern({
            "impact_analyzed": True,
            "backward_compatible": True,
            "security_reviewed": True,
            "performance_acceptable": True,
            "rollback_possible": True,
            "risk_score": 45,
            "benchmark_required": True,
            "benchmark_passed": False,
        })

        self.assertFalse(result.approved)
        self.assertIn("benchmark_passed", result.blockers)

    def test_failure_taxonomy_is_analytics_friendly(self):
        self.assertEqual(
            EngineeringMaturityEngine.failure_taxonomy(
                [{"failures": [{"failure": "ImportError: package missing"}]}]
            ),
            {"dependency": 1},
        )


if __name__ == "__main__":
    unittest.main()
