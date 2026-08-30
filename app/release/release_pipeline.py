import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

from app.benchmark.golden_benchmark_runner import GoldenBenchmarkRunner
from app.release.artifact_manager import ArtifactManager
from app.release.release_report import ReleaseReport
from app.release.security_gate import SecurityGate


class ReleasePipeline:
    """Runs deterministic release gates and emits an auditable artifact bundle."""

    def __init__(self, project_root=None, test_runner=None, benchmark_runner=None,
                 security_gate=None, report_builder=None):
        self.project_root = os.path.abspath(project_root or os.getcwd())
        self.test_runner = test_runner or self._run_tests
        self.benchmark_runner = benchmark_runner or GoldenBenchmarkRunner()
        self.security_gate = security_gate or SecurityGate()
        self.report_builder = report_builder or ReleaseReport()

    def run(self, output_root, *, version="0.1.0-alpha", label=None, package=False):
        artifacts = ArtifactManager(output_root)
        release_directory = artifacts.create_release_directory(label or f"jarvis-x-{version}")
        tests = self._normalize_test_result(self.test_runner(self.project_root))
        benchmarks = self.benchmark_runner.run()
        documentation = self._documentation_gate()
        security = self.security_gate.scan(self._security_root())
        gates = {
            "tests": {"passed": tests["success"], "summary": f"{tests['tests_run']} tests run"},
            "benchmarks": {"passed": benchmarks["quality_gate"]["passed"], "summary": f"{benchmarks['preflight_passed']}/{benchmarks['total']} preflights passed"},
            "documentation": {"passed": documentation["passed"], "summary": documentation["summary"]},
            "security": {"passed": security["passed"], "summary": f"{security['high_severity']} high-severity findings"},
        }
        manifest = {
            "success": all(gate["passed"] for gate in gates.values()),
            "version": str(version),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project_root": self.project_root,
            "gates": gates,
            "tests": tests,
            "benchmarks": benchmarks,
            "documentation": documentation,
            "security": security,
            "artifacts": [],
        }
        manifest_path = artifacts.write_json(release_directory, "release-manifest.json", manifest)
        report_path = artifacts.write_text(release_directory, "release-report.md", self.report_builder.to_markdown(manifest))
        manifest["artifacts"].extend([manifest_path, report_path])
        if package and manifest["success"]:
            package_path = self._package(release_directory, version)
            manifest["artifacts"].append(package_path)
        artifacts.write_json(release_directory, "release-manifest.json", manifest)
        return manifest

    def _documentation_gate(self):
        required = ("README.md", "CHANGELOG.md", os.path.join("docs", "golden-benchmark-suite.md"))
        missing = [item for item in required if not os.path.isfile(os.path.join(self.project_root, item))]
        return {"passed": not missing, "missing": missing, "summary": "Required release documentation is present." if not missing else "Missing: " + ", ".join(missing)}

    def _security_root(self):
        """Release gate audits shipped source, not deliberately unsafe test fixtures."""
        application = os.path.join(self.project_root, "app")
        return application if os.path.isdir(application) else self.project_root

    def _package(self, release_directory, version):
        staging = os.path.join(release_directory, "jarvis-x")
        os.makedirs(staging, exist_ok=True)
        for name in ("app", "docs", "README.md", "CHANGELOG.md", "requirements.txt"):
            source = os.path.join(self.project_root, name)
            destination = os.path.join(staging, name)
            if os.path.isdir(source):
                shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__", ".venv", "venv"))
            elif os.path.isfile(source):
                shutil.copy2(source, destination)
        return shutil.make_archive(os.path.join(release_directory, f"jarvis-x-{version}"), "zip", release_directory, "jarvis-x")

    @staticmethod
    def _normalize_test_result(result):
        if isinstance(result, dict):
            return {"success": bool(result.get("success")), "tests_run": int(result.get("tests_run", 0)), "output": str(result.get("output", ""))}
        return {"success": bool(result), "tests_run": 0, "output": ""}

    @staticmethod
    def _run_tests(project_root):
        completed = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        output = "\n".join(value for value in (completed.stdout.strip(), completed.stderr.strip()) if value)
        return {"success": completed.returncode == 0, "tests_run": ReleasePipeline._tests_run(output), "output": output}

    @staticmethod
    def _tests_run(output):
        for line in str(output).splitlines():
            if line.strip().startswith("Ran ") and " tests" in line:
                try:
                    return int(line.strip().split()[1])
                except (IndexError, ValueError):
                    return 0
        return 0
