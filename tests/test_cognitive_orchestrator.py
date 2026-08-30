import unittest

from app.cognition import CognitiveOrchestrator


class TestCognitiveOrchestrator(unittest.TestCase):
    def test_simple_request_uses_fast_plan(self):
        result = CognitiveOrchestrator().orchestrate("Add a helper function")

        self.assertEqual(result.depth, "fast")
        self.assertEqual(result.thinking_mode, "FAST")
        self.assertEqual(result.thinking_budget_ms, 200)
        self.assertEqual(result.action, "plan")
        self.assertFalse(result.simulation_required)
        self.assertEqual(result.mental_models, ["divide_and_conquer"])
        self.assertEqual(result.thought_tree.selected_branch_id, "branch-validate-first")

    def test_complex_production_request_adds_research_and_safety(self):
        result = CognitiveOrchestrator().orchestrate(
            "Design a production hospital platform and deploy it",
            context={"high_risk": True},
        )

        self.assertEqual(result.depth, "deep")
        self.assertEqual(result.thinking_mode, "EXPERT")
        self.assertEqual(result.thinking_budget_ms, 60000)
        self.assertTrue(result.research_required)
        self.assertTrue(result.verification_required)
        self.assertTrue(result.simulation_required)
        self.assertIn("architect", result.agents)
        self.assertIn("tradeoff_analysis", result.mental_models)
        self.assertEqual(result.route, "ask_user")

    def test_budget_and_mode_can_be_explicitly_controlled(self):
        result = CognitiveOrchestrator().orchestrate(
            "Implement a focused change",
            context={"thinking_mode": "deep", "thinking_budget_ms": 12000},
        )

        self.assertEqual(result.thinking_mode, "DEEP")
        self.assertEqual(result.thinking_budget_ms, 12000)

    def test_working_memory_preserves_explicit_unknowns_and_constraints(self):
        result = CognitiveOrchestrator().orchestrate(
            "Compare database options",
            context={"unknowns": ["expected load"], "constraints": ["budget"]},
        )

        self.assertEqual(result.working_memory.unknowns, ["expected load"])
        self.assertEqual(result.working_memory.constraints, ["budget"])
        self.assertTrue(result.research_required)


if __name__ == "__main__":
    unittest.main()
