"""Engineering Operating System composition root."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.eos.artifacts import EOSArtifacts
from app.eos.context import ExecutionContext
from app.eos.executor import EngineeringOS as _ExecutableEOS
from app.eos.goal import Goal
from app.eos.metrics import EOSMetrics
from app.eos.mission import Mission
from app.eos.scheduler import EOScheduler
from app.eos.state_machine import EOSState, EOSStateMachine
from app.eos.task_graph import TaskGraph


class EngineeringOS(_ExecutableEOS):
    """Initialize and execute engineering missions through injected services."""

    def start(self, goal: str) -> Dict[str, Any]:
        """Initialize an EOS mission without generating code or running agents."""
        mission_goal = Goal(goal)
        mission = Mission(mission_goal)
        context = ExecutionContext(mission=mission, status=EOSState.UNDERSTANDING.value)
        state_machine = EOSStateMachine()
        state_machine.transition(EOSState.UNDERSTANDING, "mission_started")
        scheduler = EOScheduler()
        graph = TaskGraph()
        artifacts = EOSArtifacts()
        metrics = EOSMetrics()
        context.data.update({
            "workflow": self.workflow.names(),
            "scheduler": scheduler,
            "task_graph": graph,
            "artifacts": artifacts,
            "metrics": metrics,
        })
        mission.status = EOSState.UNDERSTANDING.value
        self.event_bus.publish("EOS_STARTED", {
            "mission_id": mission.mission_id,
            "goal": mission_goal.text,
            "state": state_machine.state.value,
        })
        return {
            "status": "started",
            "mission_id": mission.mission_id,
            "goal": mission_goal.text,
            "current_state": state_machine.state.value,
            "workflow": self.workflow.names(),
            "context": context,
            "scheduler": scheduler,
            "task_graph": graph,
            "artifacts": artifacts,
            "metrics": metrics,
            "state_machine": state_machine,
        }
