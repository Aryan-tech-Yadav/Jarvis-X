"""Composable, observable stages for autonomous project-generation runs."""

from .generation_pipeline import GenerationPipeline
from .pipeline_context import PipelineContext
from .pipeline_manager import PipelineManager
from .pipeline_result import PipelineResult
from .pipeline_stage import PipelineStage
from .pipeline_state import PipelineState
from .stage_registry import StageRegistry

__all__ = ["GenerationPipeline", "PipelineContext", "PipelineManager", "PipelineResult", "PipelineStage", "PipelineState", "StageRegistry"]
from app.pipeline.task_graph import TaskGraph, TaskNode
from app.pipeline.graph_executor import GraphExecutor

__all__ = ["TaskGraph", "TaskNode", "GraphExecutor"]
