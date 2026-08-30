import tempfile
import unittest

from app.evolution import SelfEvolutionEngine


class TestSelfEvolutionFacade(unittest.TestCase):
    def test_failure_updates_rule_prompt_and_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            result = SelfEvolutionEngine(directory).process_project(
                "Hospital",
                result="FAILED",
                agent="backend",
                failures=[{
                    "category": "security",
                    "reason": "RBAC missing",
                    "fix_strategy": "Require RBAC for every multi-role application.",
                    "success": False,
                }],
            )

        self.assertEqual(result["rules"][0]["rule_id"], "rule-security")
        self.assertEqual(result["prompt_updates"][0]["reason"], "RBAC missing")
        self.assertEqual(result["skill"]["xp"], 1)

    def test_success_increases_skill_faster(self):
        with tempfile.TemporaryDirectory() as directory:
            result = SelfEvolutionEngine(directory).process_project(
                "Todo", result="SUCCESS", agent="qa"
            )

        self.assertEqual(result["skill"]["xp"], 10)
        self.assertEqual(result["skill"]["successes"], 1)


if __name__ == "__main__":
    unittest.main()
