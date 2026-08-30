"""Tests for evolution_db.py."""

import os
import tempfile

import pytest

from app.self_improvement.evolution_db import EvolutionDB, EvolutionRecord


class TestEvolutionDB:
    def setup_method(self):
        self.tmpfile = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmpfile.close()
        self.db = EvolutionDB(self.tmpfile.name)

    def teardown_method(self):
        try:
            self.db.close()
        except Exception:
            pass
        import gc
        gc.collect()
        try:
            os.unlink(self.tmpfile.name)
        except (OSError, PermissionError):
            pass

    def test_record_evolution(self):
        evolution_id = self.db.record_evolution({}, {}, [], [], 10.0)
        assert evolution_id.startswith("evo-")

    def test_get_evolution(self):
        evolution_id = self.db.record_evolution({}, {}, [], [], 10.0)
        record = self.db.get_evolution(evolution_id)
        assert record is not None
        assert record.evolution_id == evolution_id
        assert record.duration == 10.0

    def test_record_version(self):
        evolution_id = self.db.record_evolution({}, {}, [], [], 10.0)
        version_id = self.db.record_version(evolution_id, "v1", 90.0)
        assert version_id.startswith("ver-")

    def test_get_versions(self):
        evolution_id = self.db.record_evolution({}, {}, [], [], 10.0)
        self.db.record_version(evolution_id, "v1", 90.0)
        versions = self.db.get_versions(evolution_id)
        assert len(versions) == 1

    def test_get_recent_evolutions(self):
        self.db.record_evolution({}, {}, [], [], 5.0)
        self.db.record_evolution({}, {}, [], [], 3.0)
        recent = self.db.get_recent_evolutions(limit=1)
        assert len(recent) == 1

    def test_get_stats(self):
        self.db.record_evolution({}, {}, [], [], 10.0)
        stats = self.db.get_stats()
        assert stats["total_evolutions"] >= 1
