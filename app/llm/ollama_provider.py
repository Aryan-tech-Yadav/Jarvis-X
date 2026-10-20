from typing import Any, Optional

from app.llm.provider import LLMProvider
from config import MODEL


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, client=None, default_model: Optional[str] = None):
        self.client = client
        self.default_model = default_model or MODEL

    def complete(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        if self.client is None:
            import ollama
            self.client = ollama
        messages = kwargs.pop("messages", [{"role": "user", "content": prompt}])
        response = self.client.chat(
            model=model or self.default_model,
            messages=messages,
            **kwargs,
        )
        return response["message"]["content"]