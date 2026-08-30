"""Configurable EOS pipeline facade."""

from app.eos.workflow import Workflow, WorkflowStage

Pipeline = Workflow

__all__ = ["Pipeline", "Workflow", "WorkflowStage"]

