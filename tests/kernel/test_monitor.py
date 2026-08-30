"""Unit tests for Kernel Monitor and Kernel Watchdog."""

import unittest

from app.kernel.monitor import KernelMonitor
from app.kernel.watchdog import KernelWatchdog


class TestKernelMonitorAndWatchdog(unittest.TestCase):
    def test_monitor_samples_and_health_check(self):
        monitor = KernelMonitor()
        monitor.set_agent_state("planner", "Healthy")
        monitor.set_agent_state("executor", "Busy")

        snap = monitor.sample()
        self.assertIn("cpu_pct", snap)
        self.assertIn("ram_mb", snap)
        self.assertEqual(snap["agent_states"]["planner"], "Healthy")
        self.assertEqual(snap["agent_states"]["executor"], "Busy")

        health = monitor.health_check()
        self.assertTrue(health["is_healthy"])

    def test_watchdog_timeout_and_deadlock_detection(self):
        watchdog = KernelWatchdog(default_timeout_sec=0.01)
        watchdog.start_node("node_a")

        import time
        time.sleep(0.02)
        stalled = watchdog.check_timeouts()
        self.assertEqual(len(stalled), 1)
        self.assertEqual(stalled[0]["node_id"], "node_a")

        watchdog.finish_node("node_a")
        self.assertEqual(len(watchdog.check_timeouts()), 0)

        # Deadlock check
        graph_nodes = {
            "task_1": {"dependencies": {"task_2"}},
            "task_2": {"dependencies": {"task_1"}},
        }
        deadlock = watchdog.detect_deadlock(graph_nodes, completed_nodes=set())
        self.assertIsNotNone(deadlock)
        self.assertEqual(set(deadlock), {"task_1", "task_2"})
