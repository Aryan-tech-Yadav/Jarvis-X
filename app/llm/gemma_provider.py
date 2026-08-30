from app.llm.ollama_provider import OllamaProvider


class GemmaProvider(OllamaProvider):
    name = "gemma"

    def __init__(self, client=None, default_model="gemma2"):
        super().__init__(client, default_model)