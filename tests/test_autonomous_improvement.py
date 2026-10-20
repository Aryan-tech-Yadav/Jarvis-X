import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from app.evaluation import AutonomousImprovementEngine


class TestAutonomousImprovement(unittest.TestCase):
    def test_only_benchmark_improvements_are_promoted(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        project = Path(temporary.name)
        (project / "main.py").write_text("print('old')", encoding="utf-8")

        baseline = MagicMock(quality_score=80.0)
        baseline.to_dict.return_value = {"quality_score": 80.0}
        candidate = MagicMock(quality_score=90.0)
        candidate.to_dict.return_value = {"quality_score": 90.0}
        benchmark = MagicMock()
        benchmark.run_benchmark.side_effect = [baseline, candidate]
        comparator = MagicMock()
        comparator.compare.return_value = {"overall_change": 10.0, "regressions": []}
        sandboxes = MagicMock()
        sandboxes.create.return_value.sandbox_path = str(project / "sandbox")
        sandboxes.create.return_value.sandbox_id = "sandbox-1"
        sandboxes.promote.return_value = True
        versions = MagicMock()
        versions.create_version.return_value.version_id = "version-1"

        engine = AutonomousImprovementEngine(
            str(project),
            sandbox_builder=sandboxes,
            benchmark_engine=benchmark,
            comparator=comparator,
            version_manager=versions,
        )
        result = engine.improve([{"id": "reduce-latency"}], lambda *_: True)

        self.assertEqual(result["accepted"], 1)
        self.assertEqual(result["rejected"], 0)
        sandboxes.promote.assert_called_once()
        versions.create_version.assert_called_once()
        self.assertTrue(
            engine.rollback("reduce-latency")
        )
        versions.activate.assert_called_once_with("version-1")

    def test_unchanged_candidate_is_rejected_without_promotion(self):
        engine = AutonomousImprovementEngine.__new__(AutonomousImprovementEngine)
        engine.project_path = "project"
        engine.benchmark = MagicMock()
        engine.sandboxes = MagicMock()
        engine.comparator = MagicMock()
        engine.versions = MagicMock()
        baseline = MagicMock(quality_score=80.0)
        baseline.to_dict.return_value = {"quality_score": 80.0}
        engine.benchmark.run_benchmark.return_value = baseline
        engine.sandboxes.create.return_value.sandbox_path = "sandbox"
        engine.sandboxes.create.return_value.sandbox_id = "sandbox-1"

        result = engine.improve([{"id": "noop"}], lambda *_: False)

        self.assertEqual(result["rejected"], 1)
        engine.sandboxes.promote.assert_not_called()
        engine.sandboxes.discard.assert_called_once_with("sandbox-1")


if __name__ == "__main__":
    unittest.main()
