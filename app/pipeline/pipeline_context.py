from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Dict, List

from app.core.context import JarvisContext

from .pipeline_state import PipelineState


@dataclass
class PipelineContext(JarvisContext):
    """The one mutable context passed through every generation stage."""

    state: PipelineState = PipelineState.CREATED
    values: Dict[str, Any] = field(default_factory=dict)
    stage_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    completed_stages: List[str] = field(default_factory=list)
    failed_stage: str = ""

    @property
    def prompt(self):
        return self.goal

    def begin_stage(self, stage_name):
        return self.start_step(stage_name)

    def finish_stage(self, entry, result):
        success = bool(getattr(result, "success", False))
        self.finish_step(entry, success, getattr(result, "message", ""))
        name = entry["step"]
        payload = result.to_dict() if hasattr(result, "to_dict") else dict(result or {})
        self.stage_results[name] = deepcopy(payload)
        if success and name not in self.completed_stages:
            self.completed_stages.append(name)
        if not success:
            self.failed_stage = name
        self.metrics["stages_completed"] = len(self.completed_stages)
        return payload

    def merge(self, values):
        if values:
            self.values.update(dict(values))
        return self.values

    def as_dict(self):
        return {
            **super().as_dict(),
            "prompt": self.prompt,
            "state": self.state.value,
            "values": deepcopy(self.values),
            "stage_results": deepcopy(self.stage_results),
            "completed_stages": list(self.completed_stages),
            "failed_stage": self.failed_stage,
        }
