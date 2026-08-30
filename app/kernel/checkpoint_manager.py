"""Durable, JSON-only checkpoints for autonomous kernel recovery.

The checkpoint directory is deliberately supplied by the caller.  Checkpoint
identifiers are constrained to simple file names, so a project cannot cause a
checkpoint write or read outside that directory.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class CheckpointManager:
    """Store immutable checkpoint records as individual JSON files.

    All public read methods return JSON round-trip copies.  That makes a
    checkpoint safe to hand to recovery code without allowing a caller to
    mutate the persisted state by retaining a nested reference.
    """

    SCHEMA = "jarvis-x.checkpoint.v1"
    _IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

    def __init__(self, root_directory):
        if root_directory is None or not str(root_directory).strip():
            raise ValueError("Checkpoint root directory is required")
        root = Path(root_directory)
        root.mkdir(parents=True, exist_ok=True)
        if not root.is_dir():
            raise NotADirectoryError("Checkpoint root is not a directory: " + str(root))
        self.root = root.resolve()

    def create(self, stage, payload, *, checkpoint_id=None, metadata=None):
        """Create a checkpoint for ``stage`` and return its independent record."""
        if not isinstance(stage, str) or not stage.strip():
            raise ValueError("Checkpoint stage must be a non-empty string")
        checkpoint_id = checkpoint_id or self._generated_id()
        return self.save(checkpoint_id, payload, metadata=metadata, stage=stage.strip())

    def save(self, checkpoint_id, payload, *, metadata=None, stage=None):
        """Persist one checkpoint without ever overwriting an existing one."""
        checkpoint_id = self._validate_identifier(checkpoint_id)
        if stage is not None and (not isinstance(stage, str) or not stage.strip()):
            raise ValueError("Checkpoint stage must be a non-empty string when provided")

        destination = self.path_for(checkpoint_id)
        # Reject a dangling symlink as well as a normal existing checkpoint.
        if destination.exists() or destination.is_symlink():
            raise FileExistsError("Checkpoint already exists: " + checkpoint_id)

        saved_payload = self._json_copy(payload, "Checkpoint payload")
        saved_metadata = self._json_copy({} if metadata is None else metadata, "Checkpoint metadata")
        sequence = max((record["sequence"] for record in self.list()), default=0) + 1
        record = {
            "schema": self.SCHEMA,
            "id": checkpoint_id,
            "stage": stage.strip() if isinstance(stage, str) else None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "sequence": sequence,
            "metadata": saved_metadata,
            "payload": saved_payload,
        }
        self._atomic_write(destination, record)
        return self._json_copy(record, "Checkpoint record")

    def load(self, checkpoint_id):
        """Load a checkpoint record by its identifier."""
        checkpoint_id = self._validate_identifier(checkpoint_id)
        path = self.path_for(checkpoint_id)
        if not path.is_file():
            raise FileNotFoundError("Checkpoint not found: " + checkpoint_id)
        record = self._read_record(path, expected_id=checkpoint_id)
        return self._json_copy(record, "Checkpoint record")

    def list(self, stage=None):
        """Return checkpoint records in deterministic creation order.

        ``sequence`` establishes insertion order.  The timestamp and identifier
        provide deterministic tie breakers if records from another process are
        introduced concurrently.
        """
        if stage is not None and not isinstance(stage, str):
            raise TypeError("Checkpoint stage filter must be a string or None")

        records = []
        for path in self.root.iterdir():
            if not path.is_file() or path.suffix != ".json":
                continue
            checkpoint_id = path.stem
            if not self._IDENTIFIER.fullmatch(checkpoint_id):
                continue
            # Reconstruct through path_for so a symlink cannot bypass the root
            # containment assertion during a directory scan.
            safe_path = self.path_for(checkpoint_id)
            record = self._read_record(safe_path, expected_id=checkpoint_id, allow_foreign=True)
            if record is None:
                continue
            if stage is None or record["stage"] == stage:
                records.append(record)

        records.sort(key=lambda item: (item["sequence"], item["created_at"], item["id"]))
        return self._json_copy(records, "Checkpoint records")

    def latest(self, stage=None):
        """Return the most recently created checkpoint record, if any."""
        records = self.list(stage=stage)
        return self._json_copy(records[-1], "Checkpoint record") if records else None

    def path_for(self, checkpoint_id):
        """Return the validated JSON path for a checkpoint identifier."""
        checkpoint_id = self._validate_identifier(checkpoint_id)
        path = self.root / (checkpoint_id + ".json")
        self._assert_inside_root(path)
        return path

    # Clear aliases make the manager convenient for stage-oriented callers
    # without changing the simple save/load contract above.
    checkpoint_path = path_for

    def create_checkpoint(self, stage, payload, *, checkpoint_id=None, metadata=None):
        return self.create(stage, payload, checkpoint_id=checkpoint_id, metadata=metadata)

    def list_checkpoints(self, stage=None):
        return self.list(stage=stage)

    def _read_record(self, path, *, expected_id, allow_foreign=False):
        self._assert_inside_root(path)
        if path.is_symlink():
            raise ValueError("Checkpoint files cannot be symbolic links")
        try:
            with path.open("r", encoding="utf-8") as source:
                record = json.load(source)
        except json.JSONDecodeError as error:
            raise ValueError("Checkpoint is not valid JSON: " + expected_id) from error

        if not isinstance(record, dict) or record.get("schema") != self.SCHEMA:
            if allow_foreign:
                return None
            raise ValueError("Checkpoint has an unsupported schema: " + expected_id)
        if record.get("id") != expected_id:
            raise ValueError("Checkpoint identifier does not match its file name: " + expected_id)
        if not isinstance(record.get("created_at"), str):
            raise ValueError("Checkpoint is missing its creation timestamp: " + expected_id)
        if not isinstance(record.get("sequence"), int) or isinstance(record["sequence"], bool) or record["sequence"] < 1:
            raise ValueError("Checkpoint has an invalid sequence: " + expected_id)
        if "payload" not in record or "metadata" not in record:
            raise ValueError("Checkpoint is missing required data: " + expected_id)
        # A JSON round trip both validates nested structures and isolates this
        # object from the decoder before it leaves the manager.
        return self._json_copy(record, "Checkpoint record")

    def _atomic_write(self, destination, record):
        self._assert_inside_root(destination)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".checkpoint-", suffix=".tmp", dir=str(self.root))
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as temporary:
                json.dump(record, temporary, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, destination)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise

    def _assert_inside_root(self, path):
        candidate = Path(path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as error:
            raise ValueError("Checkpoint path must stay inside the checkpoint root") from error

    @classmethod
    def _validate_identifier(cls, checkpoint_id):
        if not isinstance(checkpoint_id, str) or not cls._IDENTIFIER.fullmatch(checkpoint_id):
            raise ValueError("Checkpoint identifier must be a simple file name")
        if checkpoint_id in {".", ".."}:
            raise ValueError("Checkpoint identifier is invalid")
        return checkpoint_id

    @staticmethod
    def _json_copy(value, label):
        try:
            return json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))
        except (TypeError, ValueError) as error:
            raise TypeError(label + " must be JSON serializable") from error

    @staticmethod
    def _generated_id():
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        return "checkpoint_" + timestamp + "_" + uuid4().hex[:8]
