"""Unit tests for Observability, Trust, and Production Readiness components."""

import tempfile
import unittest
from pathlib import Path

from app.observability.artifact_store import ArtifactStore
from app.observability.audit_timeline import AuditTimeline
from app.observability.decision_recorder import DecisionRecorder
from app.observability.drift_detector import DriftDetector
from app.observability.explainability_api import ExplainabilityAPI
from app.observability.mission_control import MissionControl
from app.observability.replay_engine import ReplayEngine


class TestObservabilitySuite(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_decision_recorder_and_explainability(self):
        recorder = DecisionRecorder(str(self.root / "decisions"))
        entry = recorder.record_decision(
            decision="Use FastAPI",
            reason="Best async throughput and automatic OpenAPI docs",
            alternatives=["Django", "Flask"],
            confidence=0.96,
            evidence="REST requirements + low latency target",
            stage="architecture",
        )

        self.assertEqual(entry.decision, "Use FastAPI")
        decisions = recorder.query_decisions("architecture")
        self.assertEqual(len(decisions), 1)

        explained = ExplainabilityAPI.explain_architecture({"framework": "FastAPI", "database": "PostgreSQL"})
        self.assertIn("FastAPI", explained)
        self.assertIn("PostgreSQL", explained)

    def test_audit_timeline_recording_and_markdown(self):
        timeline = AuditTimeline()
        timeline.record_event("planning", "Generate DAG", duration_sec=1.2, status="SUCCESS")
        timeline.record_event("execution", "Write Backend Code", duration_sec=4.5, status="SUCCESS")
        timeline.record_event("testing", "Run Unit Tests", duration_sec=2.1, status="SUCCESS")

        events = timeline.get_events()
        self.assertEqual(len(events), 3)

        md = timeline.to_markdown()
        self.assertIn("Audit Execution Timeline", md)
        self.assertIn("Generate DAG", md)

    def test_artifact_store_and_replay_engine(self):
        store = ArtifactStore(str(self.root / "artifacts"))
        run_id = "run-test-101"

        store.save_run_artifacts(
            run_id=run_id,
            requirements={"goal": "Build CRM"},
            plan={"steps": ["analyze", "build"]},
            timeline=[{"stage": "plan", "action": "done"}],
            quality={"overall_score": 96.0},
        )

        replay = ReplayEngine(store)
        res = replay.replay_run(run_id)
        self.assertTrue(res.success)
        self.assertEqual(res.data["events_replayed"], 1)

    def test_drift_detector_flags_regressions(self):
        detector = DriftDetector(tolerance_pct=10.0)
        baseline = {"planning_time_sec": 10.0, "quality_score": 95.0}
        current = {"planning_time_sec": 15.0, "quality_score": 80.0}

        has_drift, warnings = detector.detect_drift(current, baseline)
        self.assertTrue(has_drift)
        self.assertEqual(len(warnings), 2)

    def test_mission_control_telemetry_and_cli_view(self):
        mc = MissionControl()
        mc.update_status(
            active_project="Hospital ERP",
            current_task="Generating Dockerfile",
            completed_delta=5,
            release_progress_pct=80.0,
            quality_score=96.5,
        )

        telemetry = mc.get_telemetry()
        self.assertEqual(telemetry["active_project"], "Hospital ERP")
        self.assertEqual(telemetry["release_progress_pct"], 80.0)

        cli = mc.render_cli_view()
        self.assertIn("Hospital ERP", cli)
        self.assertIn("Mission Control Telemetry", cli)
