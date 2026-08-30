"""Unit tests for Recovery Engine and Checkpoint rollbacks."""

import tempfile
import unittest
from pathlib import Path

from app.kernel.checkpoint_manager import CheckpointManager
from app.kernel.execution_context import ExecutionContext
from app.kernel.recovery_engine import RecoveryEngine
from app.kernel.rollback_manager import RollbackManager


class TestKernelRecovery(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.checkpoints = CheckpointManager(str(self.root / "checkpoints"))
        self.rollback = RollbackManager(self.checkpoints)
        self.recovery = RecoveryEngine(self.checkpoints, self.rollback)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_checkpoint_recovery_restores_context(self):
        ctx = ExecutionContext(goal="Build API", project_id="proj_1")
        ctx.mark_completed("planning_node")

        self.checkpoints.create(
            "planning",
            {"context": ctx.to_dict(), "graph": {"nodes": ["planning_node"]}},
            checkpoint_id="cp_01",
        )

        res = self.recovery.recover("cp_01")
        self.assertTrue(res.success)
        restored_ctx = res.data["context"]
        self.assertEqual(restored_ctx.goal, "Build API")
        self.assertIn("planning_node", restored_ctx.completed_nodes)
