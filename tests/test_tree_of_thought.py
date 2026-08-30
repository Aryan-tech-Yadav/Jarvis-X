import unittest

from app.reasoning import ThoughtBranch, TreeOfThoughtEngine, WorkingMemory


class TestTreeOfThought(unittest.TestCase):
    def test_selects_safe_branch_for_risky_goal(self):
        result = TreeOfThoughtEngine().explore(
            "Deploy a production migration",
            context={"risks": ["data loss"]},
        )

        self.assertEqual(result.selected_branch_id, "branch-validate-first")
        self.assertGreaterEqual(result.selected.score, 0.9)
        self.assertTrue(any(branch.pruned for branch in result.branches))

    def test_working_memory_is_bounded_and_clamps_confidence(self):
        memory = WorkingMemory(
            "Investigate issue",
            facts=[str(index) for index in range(30)],
            confidence=2.0,
        )

        self.assertEqual(len(memory.facts), 20)
        self.assertEqual(memory.confidence, 1.0)

    def test_custom_branches_are_ranked_and_selected(self):
        result = TreeOfThoughtEngine().explore(
            "Choose an architecture",
            branch_builder=lambda *_: [
                ThoughtBranch("a", "a", ["a"], 0.5, "a"),
                ThoughtBranch("b", "b", ["b"], 0.9, "b"),
            ],
        )

        self.assertEqual(result.selected_branch_id, "b")
        self.assertEqual(result.branches[0].branch_id, "b")


if __name__ == "__main__":
    unittest.main()
