from app.llm.ollama_provider import OllamaProvider


class QwenProvider(OllamaProvider):
    name = "qwen"

    def __init__(self, client=None, default_model="qwen2.5-coder"):
        super().__init__(client, default_model)