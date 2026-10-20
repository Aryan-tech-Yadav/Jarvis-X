"""Structured project reconnaissance inspired by clean-room product analysis."""

from __future__ import annotations

import json
import re
from typing import Any

from app.ai.ai_manager import AIManager


RECON_PROMPT = """
You are a senior product architect performing clean-room reconnaissance.

Analyze this project brief and return ONLY valid JSON.
Do not claim you visited URLs or inspected sources unless evidence is supplied.
Separate evidence from assumptions. Never reproduce proprietary source code.

Project brief:
{brief}

Return this schema:
{{
  "project_summary": "short summary",
  "target_users": ["user type"],
  "screens": [
    {{
      "id": "S01",
      "name": "screen name",
      "purpose": "purpose",
      "components": ["component"],
      "states": ["loading", "empty", "success", "error"]
    }}
  ],
  "user_flows": [
    {{
      "id": "F01",
      "name": "user goal",
      "steps": ["step"],
      "edge_cases": ["edge case"]
    }}
  ],
  "entities": [
    {{
      "name": "entity",
      "fields": ["field"],
      "relationships": ["relationship"],
      "evidence": "evidence or assumption",
      "confidence": "high|medium|low"
    }}
  ],
  "features": [
    {{
      "feature": "feature name",
      "area": "area",
      "priority": "must|should|could",
      "evidence": "evidence or assumption",
      "implementation_status": "not_started"
    }}
  ],
  "out_of_scope": [
    {{"item": "item", "reason": "reason"}}
  ],
  "risks": ["risk"],
  "estimated_size": "S|M|L|XL",
  "next_steps": ["actionable next step"]
}}

Be specific, realistic, and honest about uncertainty.
"""


class ProjectReconnaissance:
    """Turn a project brief into a structured, reviewable product blueprint."""

    def __init__(self, ai: Any | None = None):
        self.ai = ai or AIManager()

    def analyze(self, brief: str) -> dict[str, Any]:
        """Analyze a brief without changing project files."""
        if not isinstance(brief, str) or not brief.strip():
            raise ValueError("Project brief must not be empty.")

        response = self.ai.ask(RECON_PROMPT.format(brief=brief.strip()))
        data = self._parse_json(response)

        required = {
            "project_summary",
            "target_users",
            "screens",
            "user_flows",
            "entities",
            "features",
            "out_of_scope",
            "risks",
            "estimated_size",
            "next_steps",
        }
        missing = required - data.keys()
        if missing:
            raise ValueError(
                "Reconnaissance response is missing fields: "
                + ", ".join(sorted(missing))
            )

        for field in ("target_users", "screens", "user_flows", "entities",
                      "features", "out_of_scope", "risks", "next_steps"):
            if not isinstance(data[field], list):
                raise ValueError(f"'{field}' must be a list.")

        for index, feature in enumerate(data["features"]):
            if not isinstance(feature, dict):
                raise ValueError(f"Feature {index} must be an object.")
            if feature.get("priority") not in {"must", "should", "could"}:
                raise ValueError(f"Feature {index} has an invalid priority.")
            feature.setdefault("implementation_status", "not_started")

        return data

    @staticmethod
    def _parse_json(response: str) -> dict[str, Any]:
        if not isinstance(response, str) or not response.strip():
            raise ValueError("AI returned an empty response.")

        text = response.strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.I)
        if fenced:
            text = fenced.group(1).strip()

        decoder = json.JSONDecoder()
        start = text.find("{")
        if start < 0:
            raise ValueError("AI response did not contain a JSON object.")

        try:
            data, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError as exc:
            raise ValueError("AI returned invalid JSON.") from exc

        if not isinstance(data, dict):
            raise ValueError("AI response must be a JSON object.")
        return data

    @staticmethod
    def render_markdown(data: dict[str, Any]) -> str:
        """Render the blueprint for human review."""
        lines = [
            "# Project Reconnaissance",
            "",
            "## Summary",
            str(data["project_summary"]),
            "",
            "## Target users",
        ]
        lines.extend(f"- {item}" for item in data["target_users"])

        lines.extend(["", "## Screen inventory"])
        for screen in data["screens"]:
            lines.append(
                f"- **{screen.get('id', '')} — {screen.get('name', '')}:** "
                f"{screen.get('purpose', '')}"
            )
            lines.append(f"  - Components: {', '.join(screen.get('components', []))}")
            lines.append(f"  - States: {', '.join(screen.get('states', []))}")

        lines.extend(["", "## User flows"])
        for flow in data["user_flows"]:
            lines.append(f"- **{flow.get('id', '')} — {flow.get('name', '')}**")
            lines.extend(f"  - {step}" for step in flow.get("steps", []))
            lines.extend(f"  - Edge case: {case}" for case in flow.get("edge_cases", []))

        lines.extend(["", "## Feature matrix", "",
                      "| Feature | Area | Priority | Evidence | Status |",
                      "|---|---|---|---|---|"])
        for feature in data["features"]:
            values = [
                feature.get("feature", ""),
                feature.get("area", ""),
                feature.get("priority", ""),
                feature.get("evidence", ""),
                feature.get("implementation_status", "not_started"),
            ]
            cells = [str(value).replace("|", "\\|").replace("\n", " ")
                     for value in values]
            lines.append("| " + " | ".join(cells) + " |")

        lines.extend(["", "## Data entities"])
        for entity in data["entities"]:
            lines.append(
                f"- **{entity.get('name', '')}:** "
                f"fields={', '.join(entity.get('fields', []))}; "
                f"confidence={entity.get('confidence', 'unknown')}; "
                f"evidence={entity.get('evidence', '')}"
            )

        lines.extend(["", "## Out of scope"])
        for item in data["out_of_scope"]:
            lines.append(f"- {item.get('item', '')}: {item.get('reason', '')}")

        lines.extend(["", "## Risks"])
        lines.extend(f"- {risk}" for risk in data["risks"])
        lines.extend(["", f"## Estimated size: {data['estimated_size']}",
                      "", "## Next steps"])
        lines.extend(f"{i}. {step}" for i, step in enumerate(data["next_steps"], 1))
        lines.append("")
        return "\n".join(lines)


    @staticmethod
    def update_feature_status(
        data: dict[str, Any],
        feature_name: str,
        status: str,
    ) -> dict[str, Any]:
        """Update one feature's implementation status."""
        allowed = {"not_started", "in_progress", "completed", "blocked"}
        if status not in allowed:
            raise ValueError(f"Invalid status: {status}")

        for feature in data.get("features", []):
            if feature.get("feature", "").casefold() == feature_name.casefold():
                feature["implementation_status"] = status
                return data

        raise ValueError(f"Feature not found: {feature_name}")

    @staticmethod
    def save_json(data: dict[str, Any], output_path: str) -> str:
        """Save reconnaissance results as JSON."""
        from pathlib import Path

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return str(path)

    @staticmethod
    def save_markdown(data: dict[str, Any], output_path: str) -> str:
        """Save the human-readable reconnaissance report."""
        from pathlib import Path

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            ProjectReconnaissance.render_markdown(data),
            encoding="utf-8",
        )
        return str(path)
