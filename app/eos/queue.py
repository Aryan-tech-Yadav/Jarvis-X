"""Queue abstraction for future external brokers."""

from queue import Queue


class EventQueue(Queue):
    """In-memory queue with a broker-compatible boundary."""
