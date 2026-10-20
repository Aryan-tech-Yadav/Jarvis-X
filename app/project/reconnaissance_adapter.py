"""Optional adapter connecting project reconnaissance to project planning."""

import json
from typing import Any

from app.project.reconnaissance import ProjectReconnaissance


class ReconnaissanceAdapter:
    """Create a reconnaissance blueprint and enrich a planning prompt."""

    def __init__(self, reconnaissance: Any | None = None):
        self.reconnaissance = reconnaissance or ProjectReconnaissance()

    def prepare_prompt(self, brief: str) -> tuple[str, dict[str, Any]]:
        """Return an enriched prompt and its structured blueprint."""
        blueprint = self.reconnaissance.analyze(brief)

        compact_blueprint = {
            "project_summary": blueprint.get("project_summary", ""),
            "target_users": blueprint.get("target_users", []),
            "screens": blueprint.get("screens", []),
            "user_flows": blueprint.get("user_flows", []),
            "entities": blueprint.get("entities", []),
            "features": blueprint.get("features", []),
            "out_of_scope": blueprint.get("out_of_scope", []),
            "risks": blueprint.get("risks", []),
            "estimated_size": blueprint.get("estimated_size", ""),
            "next_steps": blueprint.get("next_steps", []),
        }

        enriched_prompt = (
            f"Original project request:\n{brief}\n\n"
            "Use this reconnaissance blueprint as planning context. "
            "Preserve the original requirements and scope. "
            "Return the existing project-planner JSON schema only "
            "(project_name, folders, files). Do not put folders in files.\n\n"
            "Reconnaissance blueprint:\n"
            f"{json.dumps(compact_blueprint, ensure_ascii=False, indent=2)}"
        )

        return enriched_prompt, blueprint
