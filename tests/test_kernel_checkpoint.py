import tempfile
import unittest
from pathlib import Path

from app.kernel.checkpoint_manager import CheckpointManager
from app.kernel.rollback_manager import RollbackManager


class CheckpointManagerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name) / "checkpoints"
        self.manager = CheckpointManager(self.root)

    def tearDown(self):
        self.directory.cleanup()

    def test_checkpoint_is_persistent_and_isolated_from_mutable_payloads(self):
        payload = {"plan": {"steps": ["requirements"]}}
        metadata = {"project": {"id": "notes"}}
        saved = self.manager.create("planning", payload, checkpoint_id="checkpoint_01", metadata=metadata)
        payload["plan"]["steps"].append("mutated")
        metadata["project"]["id"] = "changed"
        saved["payload"]["plan"]["steps"].append("returned-mutation")

        reopened = CheckpointManager(self.root)
        loaded = reopened.load("checkpoint_01")
        self.assertEqual(loaded["stage"], "planning")
        self.assertEqual(loaded["payload"], {"plan": {"steps": ["requirements"]}})
        self.assertEqual(loaded["metadata"], {"project": {"id": "notes"}})

        loaded["payload"]["plan"]["steps"].append("load-mutation")
        self.assertEqual(reopened.load("checkpoint_01")["payload"]["plan"]["steps"], ["requirements"])

    def test_list_and_latest_follow_stable_insertion_order(self):
        self.manager.create("planning", {"step": 1}, checkpoint_id="checkpoint_01")
        self.manager.create("execution", {"step": 2}, checkpoint_id="checkpoint_02")
        reopened = CheckpointManager(self.root)

        self.assertEqual([item["id"] for item in reopened.list()], ["checkpoint_01", "checkpoint_02"])
        self.assertEqual(reopened.latest()["id"], "checkpoint_02")
        self.assertEqual(reopened.latest("planning")["id"], "checkpoint_01")

    def test_path_escape_and_unsafe_identifiers_are_rejected(self):
        outside = Path(self.directory.name) / "escaped.json"
        unsafe_ids = ("../escaped", "nested/file", "..", "", str(outside))
        for checkpoint_id in unsafe_ids:
            with self.subTest(checkpoint_id=checkpoint_id):
                with self.assertRaises(ValueError):
                    self.manager.save(checkpoint_id, {"safe": True})
        self.assertFalse(outside.exists())

        saved_path = self.manager.path_for("checkpoint_01")
        self.assertEqual(saved_path.parent.resolve(), self.root.resolve())
        self.assertTrue(saved_path.resolve().is_relative_to(self.root.resolve()))

    def test_non_json_payloads_are_refused_before_any_checkpoint_is_written(self):
        with self.assertRaises(TypeError):
            self.manager.save("invalid", {"callback": lambda: None})
        self.assertEqual(self.manager.list(), [])

    def test_existing_checkpoint_is_never_silently_overwritten(self):
        self.manager.save("checkpoint_01", {"version": 1})
        with self.assertRaises(FileExistsError):
            self.manager.save("checkpoint_01", {"version": 2})
        self.assertEqual(self.manager.load("checkpoint_01")["payload"], {"version": 1})


class RollbackManagerTests(unittest.TestCase):
    def test_rollback_selects_a_deep_copy_and_never_executes_checkpoint_contents(self):
        calls = []

        def should_never_run():
            calls.append("called")

        class Checkpoints:
            def __init__(self):
                self.record = {"id": "checkpoint_01", "payload": {"action": should_never_run}}
                self.loaded = []

            def load(self, checkpoint_id):
                self.loaded.append(checkpoint_id)
                return self.record

            def latest(self):
                return self.record

        checkpoints = Checkpoints()
        rollback = RollbackManager(checkpoints)
        selected = rollback.rollback("checkpoint_01")
        selected["payload"]["extra"] = True

        self.assertEqual(checkpoints.loaded, ["checkpoint_01"])
        self.assertNotIn("extra", checkpoints.record["payload"])
        self.assertEqual(calls, [])
        self.assertEqual(rollback.rollback()["id"], "checkpoint_01")


if __name__ == "__main__":
    unittest.main()
