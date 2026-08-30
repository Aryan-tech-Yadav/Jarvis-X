import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.engineering.autonomous_executor import AutonomousExecutor
from app.project.project_builder import ProjectBuilder


class TestRuntimeRepairRegressions(unittest.TestCase):
    def test_template_builder_can_replace_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            base_path = Path(directory) / "project"
            base_path.mkdir()
            (base_path / "old.txt").write_text("old", encoding="utf-8")

            ProjectBuilder()._build_from_template(
                {"files": {"main.py": "print('ok')"}},
                base_path=str(base_path),
            )

            self.assertEqual((base_path / "main.py").read_text(encoding="utf-8"), "print('ok')")
            self.assertFalse((base_path / "old.txt").exists())

    def test_runtime_fix_passes_file_metadata_and_persists_code(self):
        with tempfile.TemporaryDirectory() as directory:
            project_path = Path(directory)
            entry_point = project_path / "main.py"
            entry_point.write_text("raise RuntimeError('bad')", encoding="utf-8")
            executor = AutonomousExecutor()

            with patch(
                "app.project.project_runtime_fixer.ProjectRuntimeFixer.fix",
                return_value="print('fixed')",
            ) as fixer:
                self.assertTrue(executor._apply_runtime_fix(str(project_path), "bad"))

            self.assertEqual(entry_point.read_text(encoding="utf-8"), "print('fixed')")
            fixer.assert_called_once()
            self.assertEqual(fixer.call_args.args[1]["name"], "main.py")
            self.assertEqual(fixer.call_args.args[2], "raise RuntimeError('bad')")


if __name__ == "__main__":
    unittest.main()
