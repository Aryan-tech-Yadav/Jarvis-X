"""Tests for AgentTask, AgentTaskQueue, transition validation, and Dead-Letter Queue."""

import unittest

from app.agents.task import AgentTask
from app.agents.task_queue import AgentTaskQueue


class TestAgentTaskQueue(unittest.TestCase):
    def test_enqueue_dequeue_lifecycle(self):
        queue = AgentTaskQueue()
        task = AgentTask(title="Build", agent="coder", priority=10)
        self.assertTrue(task.task_id.startswith("task-"))

        queue.enqueue(task)
        self.assertEqual(len(queue), 1)

        dequeued = queue.dequeue()
        self.assertEqual(dequeued.status, "running")

        queue.complete(dequeued, result={"ok": True})
        self.assertEqual(dequeued.status, "completed")
        self.assertEqual(dequeued.result, {"ok": True})

    def test_dead_letter_queue_on_failure(self):
        queue = AgentTaskQueue()
        task = AgentTask(title="Broken", agent="tester", priority=5)

        queue.enqueue(task)
        t = queue.dequeue()
        queue.fail(t, result="assertion error")

        self.assertEqual(t.status, "failed")
        self.assertEqual(len(queue.get_dead_letter_tasks()), 1)
        self.assertEqual(queue.get_dead_letter_tasks()[0].title, "Broken")

    def test_auto_retry_then_dlq(self):
        queue = AgentTaskQueue()
        task = AgentTask(title="Retryable", agent="builder", priority=5, max_retries=2)

        queue.enqueue(task)
        # 1st attempt:
        t1 = queue.dequeue()
        queue.fail(t1, auto_retry=True)
        self.assertEqual(task.retry_count, 1)
        self.assertEqual(len(queue), 1)
        self.assertEqual(len(queue.get_dead_letter_tasks()), 0)

        # 2nd attempt:
        t2 = queue.dequeue()
        queue.fail(t2, auto_retry=True)
        self.assertEqual(task.retry_count, 2)
        self.assertEqual(len(queue), 1)
        self.assertEqual(len(queue.get_dead_letter_tasks()), 0)

        # 3rd attempt (exceeds max_retries=2):
        t3 = queue.dequeue()
        queue.fail(t3, auto_retry=True)
        self.assertEqual(len(queue), 0)
        self.assertEqual(len(queue.get_dead_letter_tasks()), 1)

    def test_transition_validation(self):
        queue = AgentTaskQueue(validate_transitions=True)
        task = AgentTask(title="Strict", agent="coder", priority=1)
        queue.enqueue(task)

        # Cannot jump from running directly to running again or invalid:
        dequeued = queue.dequeue()
        self.assertEqual(dequeued.status, "running")
        with self.assertRaises(ValueError):
            queue.enqueue(dequeued)  # cannot enqueue running task

