"""Integration test for Sprint 9 crash recovery and resume flow."""

import os
import tempfile
import unittest

from app.runtime.project_runtime import ProjectRuntime
from app.runtime.runtime_session import RuntimeSessionManager
from app.runtime.checkpoint_manager import CheckpointManager


class TestCrashResumeIntegration(unittest.TestCase):
    def test_crash_and_resume_flow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create runtime with isolated dirs
            sessions_dir = os.path.join(tmpdir, "sessions")
            ckpt_dir = os.path.join(tmpdir, "checkpoints")

            runtime = ProjectRuntime(
                session_manager=RuntimeSessionManager(sessions_dir=sessions_dir),
                checkpoint_manager=CheckpointManager(checkpoints_dir=ckpt_dir),
            )

            # Step 1: Start a new project, simulate crash after "backend" phase
            result = runtime.run("Build Hospital Management System")
            session_id = result["session_id"]
            self.assertIsNotNone(session_id)

            # Verify checkpoint exists
            ckpt_mgr = CheckpointManager(checkpoints_dir=ckpt_dir)
            latest = ckpt_mgr.latest(session_id)
            self.assertIsNotNone(latest)
            self.assertEqual(latest.phase, "reviewer")  # last phase in pipeline

            # Step 2: Resume from checkpoint
            resume_result = runtime.run("Build Hospital Management System",
                                         resume_session_id=session_id)
            self.assertIn("session_id", resume_result)
            self.assertEqual(resume_result["session_id"], session_id)

    def test_checkpoint_persists_across_instances(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ckpt_dir = os.path.join(tmpdir, "checkpoints")
            sessions_dir = os.path.join(tmpdir, "sessions")

            # First runtime instance
            runtime1 = ProjectRuntime(
                session_manager=RuntimeSessionManager(sessions_dir=sessions_dir),
                checkpoint_manager=CheckpointManager(checkpoints_dir=ckpt_dir),
            )
            result1 = runtime1.run("Build Hospital Management System")
            session_id = result1["session_id"]

            # Second runtime instance (simulates restart after crash)
            runtime2 = ProjectRuntime(
                session_manager=RuntimeSessionManager(sessions_dir=sessions_dir),
                checkpoint_manager=CheckpointManager(checkpoints_dir=ckpt_dir),
            )
            resume_result = runtime2.run("Build Hospital Management System",
                                          resume_session_id=session_id)
            self.assertEqual(resume_result["session_id"], session_id)

    def test_no_checkpoint_raises_on_resume(self):
        runtime = ProjectRuntime()
        with self.assertRaises(ValueError) as ctx:
            runtime.run("Build Hospital Management System",
                        resume_session_id="nonexistent-session")
        self.assertIn("No checkpoint found", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
