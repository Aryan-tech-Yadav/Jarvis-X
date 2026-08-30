"""Engineering architecture agent.

Combines architecture pattern selection with concrete folder structure
generation so downstream agents can materialize the project layout.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.ai.ai_manager import AIManager
from app.architecture.architecture_engine import ArchitectureEngine
from app.core.logger import Logger
from app.core.results import ExecutionResult
from app.utils.json_utils import clean_json


ARCHITECTURE_PROMPT = """
You are a senior software architect.

Given the following project requirements, produce two things:
1. A concrete folder structure for the project.
2. A high-level architecture design description.

Return ONLY valid JSON.

Schema:
{{
  "folders": [],
  "architecture": {{
    "pattern": "",
    "layers": [],
    "description": ""
  }}
}}

Folder rules:
- Include standard folders: backend/, frontend/, tests/, docs/, docker/, .github/
- If frontend is empty or not applicable, omit frontend/.
- If database migrations are needed, include backend/migrations/ or database/.
- Include a root README.md in the files list only if documentation is true.
- Return paths relative to project root. Do not include the project root itself.
- Use forward slashes. Do not include empty folders.

Architecture rules:
- pattern: one of layered monolith, clean architecture, hexagonal, mvc, microservices, serverless.
- layers: ordered list of logical layers or modules.
- description: 1-3 sentences explaining the chosen pattern and why it fits.

Project Requirements:
{requirements}
"""


@dataclass
class ArchitectureDesign:
    """Concrete architecture design with folder layout and pattern metadata."""

    folders: List[str] = field(default_factory=list)
    pattern: str = "layered monolith"
    layers: List[str] = field(default_factory=list)
    description: str = ""
    technology: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ArchitectureDesign:
        if not isinstance(data, dict):
            raise ValueError("Architecture data must be a dictionary")

        arch = data.get("architecture", {})
        if not isinstance(arch, dict):
            arch = {}

        folders = data.get("folders", [])
        if not isinstance(folders, list):
            folders = [str(folders)]

        return cls(
            folders=[str(f).strip().rstrip("/") for f in folders if str(f).strip()],
            pattern=str(arch.get("pattern", "layered monolith")).strip(),
            layers=[str(l).strip() for l in arch.get("layers", []) if str(l).strip()],
            description=str(arch.get("description", "")).strip(),
            technology=data.get("technology", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "folders": list(self.folders),
            "architecture": {
                "pattern": self.pattern,
                "layers": list(self.layers),
                "description": self.description,
            },
            "technology": dict(self.technology),
        }


class ArchitectureAgent:
    """Design the project architecture and folder structure.

    Uses the existing architecture engine for pattern/technology selection
    and an LLM prompt to produce a concrete, buildable folder layout.
    """

    def __init__(self, ai=None, engine=None):
        self.ai = ai or AIManager()
        self.engine = engine or ArchitectureEngine()

    def design(self, requirements: Dict[str, Any]) -> ExecutionResult:
        if not isinstance(requirements, dict):
            return ExecutionResult.failed("Requirements must be a dictionary")

        # First, use the existing architecture engine for pattern/technology
        try:
            engine_plan = self.engine.design(requirements)
        except Exception as exc:
            Logger.warning(f"Architecture engine failed: {exc}")
            engine_plan = {}

        # Then, use LLM to generate concrete folder structure
        prompt = ARCHITECTURE_PROMPT.format(requirements=json.dumps(requirements, indent=2))
        try:
            response = self.ai.ask(prompt)
            cleaned = clean_json(response)
            extracted = self._extract_json(cleaned) or cleaned
            data = json.loads(extracted)
            design = ArchitectureDesign.from_dict(data)

            # Merge engine insights
            if not design.pattern and engine_plan.get("pattern"):
                design.pattern = engine_plan["pattern"]
            if not design.technology:
                design.technology = engine_plan.get("technology", {})

            # Ensure standard folders exist
            self._ensure_standard_folders(design, requirements)

            return ExecutionResult.completed(
                data=design.to_dict(),
                message="Architecture designed",
                metrics={
                    "pattern": design.pattern,
                    "folders": len(design.folders),
                    "layers": len(design.layers),
                },
            )
        except Exception as exc:
            Logger.error(f"Architecture agent failed: {exc}")
            # Fallback to a minimal folder structure
            fallback = self._fallback_design(requirements)
            return ExecutionResult.completed(
                data=fallback.to_dict(),
                message="Architecture designed with fallback",
                metrics={"pattern": fallback.pattern, "folders": len(fallback.folders), "layers": len(fallback.layers)},
                warnings=[f"LLM architecture generation failed: {exc}"],
            )

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """Extract the first JSON object from text using brace matching."""
        if not text or "{" not in text:
            return None
        
        start = text.find("{")
        if start == -1:
            return None
        
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start, len(text)):
            char = text[i]
            
            if escape_next:
                escape_next = False
                continue
                
            if char == "\\" and in_string:
                escape_next = True
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
                
            if in_string:
                continue
                
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        
        return None

    @staticmethod
    def _ensure_standard_folders(design: ArchitectureDesign, requirements: Dict[str, Any]):
        standard = ["backend", "tests", "docs"]
        frontend = requirements.get("frontend", "")
        if frontend and frontend.strip():
            standard.append("frontend")
        if requirements.get("docker", False):
            standard.append("docker")
        if requirements.get("testing", False):
            standard.append("tests")

        for folder in standard:
            if folder not in design.folders:
                design.folders.append(folder)

        # Ensure layers are populated
        if not design.layers:
            design.layers = ["presentation", "application", "domain", "infrastructure"]

    @staticmethod
    def _fallback_design(requirements: Dict[str, Any]) -> ArchitectureDesign:
        folders = ["backend", "tests", "docs"]
        frontend = requirements.get("frontend", "")
        if frontend and str(frontend).strip():
            folders.append("frontend")
        if requirements.get("docker", False):
            folders.append("docker")

        return ArchitectureDesign(
            folders=folders,
            pattern="layered monolith",
            layers=["presentation", "application", "domain", "infrastructure"],
            description="Default layered monolith for rapid delivery.",
        )
