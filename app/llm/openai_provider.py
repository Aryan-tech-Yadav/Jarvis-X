from typing import Any, Optional

from app.llm.provider import LLMProvider


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, client=None, default_model="gpt-4o-mini"):
        self.client = client
        self.default_model = default_model

    def complete(self, prompt: str, model: Optional[str] = None, **kwargs: Any) -> str:
        if self.client is None:
            from openai import OpenAI
            self.client = OpenAI()
        messages = kwargs.pop("messages", [{"role": "user", "content": prompt}])
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            **kwargs,
        )
        return response.choices[0].message.content