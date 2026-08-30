"""Non-executing checkpoint selection for recovery flows."""

from __future__ import annotations

import copy


class RollbackManager:
    """Select a saved checkpoint without applying it to a workspace.

    Applying restored state belongs to the kernel/recovery layer.  Keeping this
    class read-only ensures a request to inspect or select a rollback target
    cannot accidentally execute a tool, mutate a project, or overwrite files.
    """

    def __init__(self, checkpoint_manager):
        if not callable(getattr(checkpoint_manager, "load", None)) or not callable(
                getattr(checkpoint_manager, "latest", None)):
            raise TypeError("RollbackManager requires a checkpoint manager with load and latest methods")
        self.checkpoints = checkpoint_manager

    def rollback(self, checkpoint_id=None):
        """Return a detached checkpoint record for the requested rollback target.

        With no identifier, the latest checkpoint is selected.  No callback,
        executor, workspace, or file operation is accepted or invoked here.
        """
        checkpoint = self.checkpoints.latest() if checkpoint_id is None else self.checkpoints.load(checkpoint_id)
        return copy.deepcopy(checkpoint) if checkpoint is not None else None

    def rollback_to(self, checkpoint_id):
        """Explicit spelling for callers that always select a named checkpoint."""
        return self.rollback(checkpoint_id)
