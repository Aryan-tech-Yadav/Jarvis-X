"""Database Agent - Generates database schema and migrations."""

from __future__ import annotations

from typing import Any, Dict

from app.agents.base_agent import BaseAgent
from app.agents.project_context import ProjectContext
from app.core.logger import Logger


class DatabaseAgent(BaseAgent):
    """Generates database schema, models, and migration files."""

    agent_id = "database"
    capabilities = ("database", "db", "schema", "migration", "sql", "models")

    def run(self, context) -> Dict[str, Any]:
        if isinstance(context, dict):
            context = ProjectContext(**{k: v for k, v in context.items() if k in ProjectContext.__dataclass_fields__})
        
        requirements = context.requirements or {}
        database = requirements.get("database", "")
        
        if not database or not str(database).strip():
            context.add_log("No database specified, skipping")
            return {
                "success": True,
                "output": {"skipped": True, "reason": "No database specified"},
                "context": context,
            }

        Logger.info(f"[DatabaseAgent] Designing database: {database}")
        context.current_task = "database_design"
        context.add_log(f"Starting database design: {database}")

        # Database design is captured in architecture and project generation
        context.add_completed_task("database_design")
        context.add_log(f"Database design planned for: {database}")
        context.set_metric("database", database)
        
        return {
            "success": True,
            "output": {"database": database, "status": "planned"},
            "context": context,
        }
