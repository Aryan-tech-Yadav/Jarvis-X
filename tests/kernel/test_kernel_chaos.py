"""Enterprise Chaos Testing for Kernel Resilience."""

import tempfile
import unittest
from pathlib import Path

from app.core.results import ExecutionResult
from app.kernel.execution_context import ExecutionContext
from app.kernel.execution_graph import ExecutionGraph
from app.kernel.kernel import AutonomousExecutionKernel


class TestKernelChaosResilience(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.kernel = AutonomousExecutionKernel(
            checkpoint_dir=str(Path(self.temp_dir.name) / "cps"),
            default_retries=2,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_chaos_handler_failure_with_retry_recovery(self):
        attempts = {"count": 0}

        def flaky_handler(context, node):
            attempts["count"] += 1
            if attempts["count"] < 2:
                return ExecutionResult.failed("Simulated transient node crash")
            return ExecutionResult.completed(data={"healed": True})

        graph = ExecutionGraph()
        graph.add_node("flaky_task", payload={"max_retries": 2})

        self.kernel.register_handler("flaky_task", flaky_handler)
        ctx = ExecutionContext(goal="Chaos Test")

        result = self.kernel.execute(graph, ctx)
        self.assertTrue(result.success)
        self.assertEqual(attempts["count"], 2)
        self.assertIn("flaky_task", ctx.completed_nodes)

    def test_chaos_unrecoverable_failure_halts_cleanly(self):
        def crashing_handler(context, node):
            return ExecutionResult.failed("Fatal unrecoverable error")

        graph = ExecutionGraph()
        graph.add_node("fatal_task", payload={"max_retries": 0})

        self.kernel.register_handler("fatal_task", crashing_handler)
        ctx = ExecutionContext(goal="Chaos Fatal Test")

        result = self.kernel.execute(graph, ctx)
        self.assertFalse(result.success)
        self.assertEqual(ctx.failed_node, "fatal_task")
