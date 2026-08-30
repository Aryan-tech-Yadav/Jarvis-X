"""Unit tests for Kernel Boot Manager."""

import unittest

from app.core.registry import ModuleRegistry
from app.kernel.boot_manager import KernelBootManager


class TestKernelBootManager(unittest.TestCase):
    def test_deterministic_boot_order(self):
        registry = ModuleRegistry()
        init_order = []

        class Component:
            def __init__(self, name):
                self.name = name

            def initialize(self, context=None):
                init_order.append(self.name)
                return True

            def shutdown(self, context=None):
                return True

        registry.register("runtime", Component("runtime"))
        registry.register("event_bus", Component("event_bus"))
        registry.register("dispatcher", Component("dispatcher"))

        boot = KernelBootManager(registry)
        res = boot.boot()
        self.assertTrue(res.success)
        self.assertEqual(init_order, ["event_bus", "runtime", "dispatcher"])

    def test_shutdown_in_reverse_order(self):
        registry = ModuleRegistry()
        shutdown_order = []

        class Component:
            def __init__(self, name):
                self.name = name

            def initialize(self):
                return True

            def shutdown(self):
                shutdown_order.append(self.name)
                return True

        registry.register("event_bus", Component("event_bus"))
        registry.register("runtime", Component("runtime"))

        boot = KernelBootManager(registry)
        boot.boot()
        res = boot.shutdown()
        self.assertTrue(res.success)
        self.assertEqual(shutdown_order, ["runtime", "event_bus"])
