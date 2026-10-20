import time
from typing import Any, Dict, Optional

from app.llm.cost_tracker import CostTracker
from app.llm.latency_tracker import LatencyTracker
from app.llm.model_selector import ModelSelector
from app.llm.ollama_provider import OllamaProvider
from config import MODEL


class LLMRouter:
    def __init__(self, providers=None, selector=None, cost_tracker=None, latency_tracker=None):
        self.providers = dict(providers or {"ollama": OllamaProvider()})
        self.selector = selector or ModelSelector()
        self.cost_tracker = cost_tracker or CostTracker()
        self.latency_tracker = latency_tracker or LatencyTracker()

    def register(self, name: str, provider):
        if not name or not callable(getattr(provider, "complete", None)):
            raise ValueError("A provider name and complete() implementation are required")
        self.providers[name] = provider

    def ask(self, prompt: str, task_type="general", provider: Optional[str] = None, model: Optional[str] = None, **kwargs: Any) -> str:
        names = [provider] if provider else list(self.providers)
        if not provider and self.selector.models:
            selected = self.selector.select(task_type, names)
            names = [selected] + [name for name in names if name != selected]
        errors = []
        for name in names:
            current = self.providers.get(name)
            if current is None:
                continue
            chosen_model = model or (MODEL if name == "ollama" else None)
            started = time.perf_counter()
            provider_kwargs = dict(kwargs)
            cost = provider_kwargs.pop("cost", 0.0)
            try:
                answer = current.complete(prompt, model=chosen_model, **provider_kwargs)
                self.latency_tracker.record(chosen_model or name, time.perf_counter() - started)
                self.cost_tracker.record(chosen_model or name, cost)
                return answer
            except Exception as error:
                errors.append(f"{name}: {error}")
        raise RuntimeError("All LLM providers failed: " + "; ".join(errors))