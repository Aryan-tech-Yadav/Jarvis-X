from app.llm.ollama_provider import OllamaProvider


class DeepSeekProvider(OllamaProvider):
    name = "deepseek"

    def __init__(self, client=None, default_model="deepseek-coder"):
        super().__init__(client, default_model)