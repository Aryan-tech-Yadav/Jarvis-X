import json

from app.ai.ai_manager import AIManager
from app.prompts.intent_prompt import INTENT_PROMPT
from app.utils.json_utils import clean_json


class IntentClassifier:

    SUPPORTED_INTENTS = {
        "CREATE_PROJECT",
        "MODIFY_PROJECT",
        "ANALYZE_PROJECT",
        "GENERAL_CHAT",
        "HELP",
        "EXIT",
    }

    def __init__(self, ai=None):
        self.ai = ai or AIManager()

    def classify(self, user_input):
        if not isinstance(user_input, str) or not user_input.strip():
            return {"intent": "GENERAL_CHAT", "request": ""}

        prompt = INTENT_PROMPT.format(user_input=user_input.strip())
        try:
            result = json.loads(clean_json(self.ai.ask(prompt)))
        except Exception:
            return self._fallback(user_input)

        intent = result.get("intent")
        request = result.get("request", user_input.strip())
        if intent not in self.SUPPORTED_INTENTS or not isinstance(request, str):
            return self._fallback(user_input)

        return {"intent": intent, "request": request.strip()}

    def _fallback(self, user_input):
        text = user_input.strip().lower()
        if text in {"exit", "quit"}:
            intent = "EXIT"
        elif text == "help":
            intent = "HELP"
        elif text == "analyze":
            intent = "ANALYZE_PROJECT"
        elif text.startswith(("create ", "build ")):
            intent = "CREATE_PROJECT"
        elif text.startswith(("modify ", "add ", "fix ", "remove ", "use ")):
            intent = "MODIFY_PROJECT"
        else:
            intent = "GENERAL_CHAT"
        return {"intent": intent, "request": user_input.strip()}
