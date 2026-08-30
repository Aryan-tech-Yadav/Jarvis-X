from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(init=False)
class Thought:
    thought: str
    tool: str
    action: str
    arguments: Dict[str, Any]
    finished: bool
    step: int
    confidence: float
    reasoning: str

    def __init__(self, thought=None, tool="", action="", arguments=None, finished=False, step=1,
                 text=None, confidence=1.0, reasoning=""):
        self.thought = text if text is not None else (thought or "")
        self.tool = tool
        self.action = action
        self.arguments = arguments or {}
        self.finished = finished
        self.step = step
        self.confidence = confidence
        self.reasoning = reasoning

    @property
    def text(self):
        return self.thought

    def to_dict(self):
        return {
            "thought": self.thought,
            "tool": self.tool,
            "action": self.action,
            "input": self.arguments,
            "arguments": self.arguments,
            "finished": self.finished,
            "step": self.step,
            "text": self.text,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
        }
