import json

from app.ai.ai_manager import AIManager
from app.prompts.reflection_prompt import REFLECTION_PROMPT
from app.utils.json_utils import clean_json
from app.reflection.reflection_report import ReflectionReport
from app.reflection.reflection_score import ReflectionScore


class ReflectionAgent:

    def __init__(self, ai=None):
        self.ai = ai or AIManager()

    def reflect(self, step, summary, execution_result, validation_message):
        prompt = REFLECTION_PROMPT.format(
            step=step,
            summary=summary,
            execution_result=execution_result,
            validation_message=validation_message,
        )
        try:
            result = json.loads(clean_json(self.ai.ask(prompt)))
        except Exception:
            return self._fallback()

        if not isinstance(result, dict):
            return self._fallback()

        needs_repair = result.get("needs_repair")
        next_action = result.get("next_action")
        if not isinstance(needs_repair, bool) or next_action not in {"continue", "repair"}:
            return self._fallback()

        return {
            "success": bool(result.get("success", not needs_repair)),
            "needs_repair": needs_repair,
            "feedback": str(result.get("feedback", "")),
            "next_action": next_action,
        }

    def _fallback(self):
        return {
            "success": True,
            "needs_repair": False,
            "feedback": "Reflection response was invalid; continuing after validation.",
            "next_action": "continue",
        }

    def scorecard(self, scores, notes=None):
        """Build a deterministic, category-level reflection for dashboards and learning."""
        return ReflectionReport(ReflectionScore.from_mapping(scores), notes).to_dict()
