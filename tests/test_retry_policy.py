"""Tests for RetryPolicy, exponential backoff, and CircuitBreaker."""

import time
import unittest

from app.recovery.retry_policy import CircuitBreaker, RetryPolicy


class TestCircuitBreaker(unittest.TestCase):
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker()
        self.assertEqual(cb.get_state("api"), CircuitBreaker.STATE_CLOSED)
        self.assertTrue(cb.allow_request("api"))

    def test_trips_to_open_after_threshold(self):
        cb = CircuitBreaker(failure_threshold=3)
        self.assertFalse(cb.record_failure("api"))  # 1
        self.assertFalse(cb.record_failure("api"))  # 2
        tripped = cb.record_failure("api")          # 3
        self.assertTrue(tripped)
        self.assertEqual(cb.get_state("api"), CircuitBreaker.STATE_OPEN)
        self.assertFalse(cb.allow_request("api"))

    def test_transitions_to_half_open_after_cooldown(self):
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.02)
        cb.record_failure("db")
        cb.record_failure("db")
        self.assertEqual(cb.get_state("db"), CircuitBreaker.STATE_OPEN)

        time.sleep(0.04)
        self.assertEqual(cb.get_state("db"), CircuitBreaker.STATE_HALF_OPEN)
        self.assertTrue(cb.allow_request("db"))

    def test_half_open_success_resets_to_closed(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.02, half_open_success_threshold=1)
        cb.record_failure("network")
        self.assertEqual(cb.get_state("network"), CircuitBreaker.STATE_OPEN)

        time.sleep(0.04)
        self.assertEqual(cb.get_state("network"), CircuitBreaker.STATE_HALF_OPEN)

        cb.record_success("network")
        self.assertEqual(cb.get_state("network"), CircuitBreaker.STATE_CLOSED)
        self.assertTrue(cb.allow_request("network"))

    def test_half_open_failure_reopens_immediately(self):
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.02)
        cb.record_failure("llm")
        time.sleep(0.04)
        self.assertEqual(cb.get_state("llm"), CircuitBreaker.STATE_HALF_OPEN)

        cb.record_failure("llm")
        self.assertEqual(cb.get_state("llm"), CircuitBreaker.STATE_OPEN)
        self.assertFalse(cb.allow_request("llm"))


class TestRetryPolicy(unittest.TestCase):
    def test_default_category_limits(self):
        policy = RetryPolicy()
        self.assertTrue(policy.can_retry("research", 4))
        self.assertFalse(policy.can_retry("research", 5))
        self.assertTrue(policy.can_retry("runtime", 3))
        self.assertFalse(policy.can_retry("runtime", 4))

    def test_circuit_breaker_integration(self):
        cb = CircuitBreaker(failure_threshold=2)
        policy = RetryPolicy(circuit_breaker=cb)

        self.assertTrue(policy.can_retry("runtime", 1))
        cb.record_failure("runtime")
        cb.record_failure("runtime")

        # Even though attempt 1 < 4, circuit breaker is tripped:
        self.assertFalse(policy.can_retry("runtime", 1))

    def test_compute_backoff_calculation(self):
        policy = RetryPolicy()
        d1 = policy.compute_backoff(attempt=1, base_delay=1.0, jitter=False)
        d2 = policy.compute_backoff(attempt=2, base_delay=1.0, jitter=False)
        d3 = policy.compute_backoff(attempt=3, base_delay=1.0, jitter=False)

        self.assertEqual(d1, 1.0)
        self.assertEqual(d2, 2.0)
        self.assertEqual(d3, 4.0)

    def test_compute_backoff_with_jitter_within_bounds(self):
        policy = RetryPolicy()
        for attempt in range(1, 5):
            delay = policy.compute_backoff(attempt=attempt, base_delay=2.0, max_delay=30.0, jitter=True)
            self.assertGreater(delay, 0)
            self.assertLessEqual(delay, 30.0)
