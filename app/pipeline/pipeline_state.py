from enum import Enum


class PipelineState(str, Enum):
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    FAILED = "failed"
    RECOVERING = "recovering"
    FINISHED = "finished"
