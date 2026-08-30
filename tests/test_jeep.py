import tempfile
import unittest
from pathlib import Path

from app.evaluation import EngineeringEvaluationPlatform


class TestJEEP(unittest.TestCase):
    def _project(self, code="print('ok')"):
        directory = tempfile.TemporaryDirectory()
        path = Path(directory.name)
        (path / "main.py").write_text(code, encoding="utf-8")
        return directory, path

    def test_evaluation_scores_project_and_records_learning(self):
        temporary, path = self._project()
        self.addCleanup(temporary.cleanup)

        platform = EngineeringEvaluationPlatform()
        result = platform.evaluate_project("demo", str(path), version="v1")

        self.assertIn("quality", result)
        self.assertIn("reliability", result)
        self.assertIn("wisdom", result)
        self.assertIn("best_decision", result["wisdom"]["questions"])
        self.assertEqual(len(platform.records()), 1)
        self.assertEqual(result["evolution"]["skill"]["agent"], "engineering")

    def test_failure_is_diagnosed_and_blocks_success(self):
        temporary, path = self._project()
        self.addCleanup(temporary.cleanup)

        result = EngineeringEvaluationPlatform().evaluate_project(
            "demo",
            str(path),
            version="v1",
            failures=[{"message": "NameError: name 'shutil' is not defined"}],
        )

        self.assertFalse(result["quality"]["passed_gate"] is False and result["reliability"]["success"])
        self.assertEqual(result["failures"][0]["error_category"], "name")
        self.assertEqual(result["reliability"]["success"], False)
        self.assertIn("shutil", result["wisdom"]["questions"]["costliest_mistake"])

    def test_wisdom_answers_can_be_overridden_without_losing_evidence(self):
        temporary, path = self._project()
        self.addCleanup(temporary.cleanup)

        result = EngineeringEvaluationPlatform().evaluate_project(
            "demo",
            str(path),
            version="v1",
            wisdom_answers={"reusable_principle": "Always benchmark before replacing a planner."},
        )

        self.assertEqual(
            result["wisdom"]["questions"]["reusable_principle"],
            "Always benchmark before replacing a planner.",
        )
        self.assertIn("quality_score", result["wisdom"]["evidence"])

    def test_comparison_reports_regression(self):
        first, path = self._project()
        self.addCleanup(first.cleanup)
        platform = EngineeringEvaluationPlatform()
        platform.evaluate_project("demo", str(path), version="v1")
        (path / "main.py").write_text("raise RuntimeError('broken')", encoding="utf-8")
        platform.evaluate_project("demo", str(path), version="v2")

        comparison = platform.compare_versions("v2", "v1")

        self.assertFalse(comparison["better"])
        self.assertIn("runtime_score", comparison["regressions"])


if __name__ == "__main__":
    unittest.main()
