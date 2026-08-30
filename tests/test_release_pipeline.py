import json
import os
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from app.release.artifact_manager import ArtifactManager
from app.release.release_pipeline import ReleasePipeline
from app.release.security_gate import SecurityGate


class ArtifactManagerTests(unittest.TestCase):
    def test_artifact_manager_writes_json_and_text_inside_output_root(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ArtifactManager(directory)
            release = manager.create_release_directory("candidate-1")
            json_path = manager.write_json(release, "manifest.json", {"success": True})
            text_path = manager.write_text(release, "report.md", "# Report")
            with open(json_path, "r", encoding="utf-8") as file:
                self.assertTrue(json.load(file)["success"])
            self.assertTrue(os.path.isfile(text_path))

    def test_artifact_manager_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = ArtifactManager(directory)
            with self.assertRaises(ValueError):
                manager.write_text(os.path.dirname(directory), "report.md", "bad")
            with self.assertRaises(ValueError):
                manager.write_text(directory, "../report.md", "bad")

    def test_artifact_manager_rejects_unsafe_release_label(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                ArtifactManager(directory).create_release_directory("...")


class SecurityGateTests(unittest.TestCase):
    def test_security_gate_passes_clean_source_and_counts_files(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "safe.py"), "w", encoding="utf-8") as file:
                file.write("def run(value):\n    return value + 1\n")
            report = SecurityGate().scan(directory)
        self.assertTrue(report["passed"])
        self.assertEqual(report["files_scanned"], 1)

    def test_security_gate_detects_dynamic_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "unsafe.py"), "w", encoding="utf-8") as file:
                file.write("eval('1 + 1')\n")
            report = SecurityGate().scan(directory)
        self.assertFalse(report["passed"])
        self.assertEqual(report["findings"][0]["rule"], "dynamic_execution")

    def test_security_gate_detects_hardcoded_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "unsafe.py"), "w", encoding="utf-8") as file:
                file.write("api_key = 'abcdefghi'\n")
            report = SecurityGate().scan(directory)
        self.assertFalse(report["passed"])
        self.assertEqual(report["findings"][0]["rule"], "hardcoded_secret")

    def test_security_gate_ignores_virtual_environment_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            os.makedirs(os.path.join(directory, ".venv"))
            with open(os.path.join(directory, ".venv", "unsafe.py"), "w", encoding="utf-8") as file:
                file.write("eval('1 + 1')\n")
            self.assertTrue(SecurityGate().scan(directory)["passed"])


class ReleasePipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = self.directory.name
        os.makedirs(os.path.join(self.root, "docs"))
        os.makedirs(os.path.join(self.root, "app"))
        for path, content in {
            "README.md": "# Demo\n",
            "CHANGELOG.md": "# Changes\n",
            "requirements.txt": "\n",
            os.path.join("docs", "golden-benchmark-suite.md"): "# Benchmarks\n",
            os.path.join("app", "safe.py"): "VALUE = 1\n",
        }.items():
            with open(os.path.join(self.root, path), "w", encoding="utf-8") as file:
                file.write(content)

    def tearDown(self):
        self.directory.cleanup()

    @staticmethod
    def _benchmarks(passed=True):
        return type("Benchmarks", (), {"run": lambda self: {
            "total": 20, "preflight_passed": 20 if passed else 10,
            "preflight_rate": 1.0 if passed else 0.5, "approval_required": 2,
            "quality_gate": {"passed": passed},
        }})()

    def test_release_pipeline_writes_manifest_and_markdown_report(self):
        pipeline = ReleasePipeline(
            self.root,
            test_runner=lambda root: {"success": True, "tests_run": 42, "output": "ok"},
            benchmark_runner=self._benchmarks(),
        )
        result = pipeline.run(os.path.join(self.root, "artifacts"), label="candidate")
        self.assertTrue(result["success"])
        self.assertEqual(len(result["artifacts"]), 2)
        self.assertTrue(all(os.path.isfile(path) for path in result["artifacts"]))
        self.assertTrue(result["gates"]["security"]["passed"])

    def test_release_pipeline_blocks_failed_tests_but_still_emits_reports(self):
        pipeline = ReleasePipeline(
            self.root,
            test_runner=lambda root: {"success": False, "tests_run": 3, "output": "failure"},
            benchmark_runner=self._benchmarks(),
        )
        result = pipeline.run(os.path.join(self.root, "artifacts"), label="failed-tests")
        self.assertFalse(result["success"])
        self.assertFalse(result["gates"]["tests"]["passed"])
        self.assertTrue(os.path.isfile(result["artifacts"][0]))

    def test_release_pipeline_blocks_failed_benchmark_gate(self):
        pipeline = ReleasePipeline(self.root, test_runner=lambda root: True, benchmark_runner=self._benchmarks(False))
        result = pipeline.run(os.path.join(self.root, "artifacts"), label="failed-benchmark")
        self.assertFalse(result["success"])
        self.assertFalse(result["gates"]["benchmarks"]["passed"])

    def test_release_pipeline_blocks_missing_documentation(self):
        os.remove(os.path.join(self.root, "CHANGELOG.md"))
        pipeline = ReleasePipeline(self.root, test_runner=lambda root: True, benchmark_runner=self._benchmarks())
        result = pipeline.run(os.path.join(self.root, "artifacts"), label="missing-docs")
        self.assertFalse(result["success"])
        self.assertFalse(result["gates"]["documentation"]["passed"])

    def test_release_pipeline_blocks_security_findings(self):
        with open(os.path.join(self.root, "app", "unsafe.py"), "w", encoding="utf-8") as file:
            file.write("exec('x = 1')\n")
        pipeline = ReleasePipeline(self.root, test_runner=lambda root: True, benchmark_runner=self._benchmarks())
        result = pipeline.run(os.path.join(self.root, "artifacts"), label="unsafe")
        self.assertFalse(result["success"])
        self.assertFalse(result["gates"]["security"]["passed"])

    def test_release_security_gate_does_not_treat_test_fixtures_as_shipped_source(self):
        os.makedirs(os.path.join(self.root, "tests"))
        with open(os.path.join(self.root, "tests", "unsafe_fixture.py"), "w", encoding="utf-8") as file:
            file.write("api_key = 'test-fixture-value'\n")
        pipeline = ReleasePipeline(self.root, test_runner=lambda root: True, benchmark_runner=self._benchmarks())
        result = pipeline.run(os.path.join(self.root, "artifacts"), label="fixture")
        self.assertTrue(result["gates"]["security"]["passed"])

    def test_release_pipeline_only_packages_a_passing_release(self):
        pipeline = ReleasePipeline(self.root, test_runner=lambda root: True, benchmark_runner=self._benchmarks())
        result = pipeline.run(os.path.join(self.root, "artifacts"), label="packaged", package=True)
        package = next(path for path in result["artifacts"] if path.endswith(".zip"))
        self.assertTrue(zipfile.is_zipfile(package))

    def test_test_result_normalizer_handles_boolean_results(self):
        self.assertEqual(ReleasePipeline._normalize_test_result(True)["tests_run"], 0)

    def test_test_count_parser_handles_unittest_output(self):
        self.assertEqual(ReleasePipeline._tests_run("Ran 247 tests in 2.0s"), 247)


class ReleaseCliTests(unittest.TestCase):
    def test_release_cli_returns_zero_for_passing_pipeline(self):
        from app.release import cli

        class Pipeline:
            def run(self, output, version, package):
                return {"success": True, "artifacts": ["release.zip"]}

        with patch.object(cli, "ReleasePipeline", return_value=Pipeline()):
            self.assertEqual(cli.main(["release", "--output", "out"]), 0)

    def test_release_cli_returns_one_for_blocked_pipeline(self):
        from app.release import cli

        class Pipeline:
            def run(self, output, version, package):
                return {"success": False, "artifacts": ["manifest.json"]}

        with patch.object(cli, "ReleasePipeline", return_value=Pipeline()):
            self.assertEqual(cli.main(["release"]), 1)


if __name__ == "__main__":
    unittest.main()
