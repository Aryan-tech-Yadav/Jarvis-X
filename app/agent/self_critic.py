import json

from app.ai.ai_manager import AIManager
from app.prompts.self_critic_prompt import SELF_CRITIC_PROMPT
from app.utils.json_utils import clean_json


class SelfCritic:

    def __init__(self, ai=None):
        self.ai = ai or AIManager()

    def review(self, step, summary, validation_message):
        prompt = SELF_CRITIC_PROMPT.format(
            step=step,
            summary=summary,
            validation_message=validation_message,
        )
        try:
            result = json.loads(clean_json(self.ai.ask(prompt)))
        except (json.JSONDecodeError, TypeError, AttributeError):
            return self._fallback()

        if not isinstance(result, dict):
            return self._fallback()

        approved = result.get("approved")
        issues = result.get("issues")
        score = result.get("score")
        if (
            not isinstance(approved, bool)
            or not isinstance(issues, list)
            or not all(isinstance(issue, str) for issue in issues)
            or not isinstance(score, (int, float))
            or not 0 <= score <= 10
        ):
            return self._fallback()

        return {
            "approved": approved,
            "issues": [issue.strip() for issue in issues if issue.strip()],
            "score": score,
        }

    def _fallback(self):
        return {
            "approved": True,
            "issues": [],
            "score": 5.0,
        }
