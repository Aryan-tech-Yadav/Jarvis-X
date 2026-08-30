"""Registry for replaceable strategy plugins."""

from typing import Dict, Iterable, List

from .base_strategy import BaseStrategy


class StrategyRegistry:
    def __init__(self, strategies: Iterable[BaseStrategy] | None = None):
        self._strategies: Dict[str, BaseStrategy] = {}
        for strategy in strategies or ():
            self.register(strategy)

    def register(self, strategy: BaseStrategy) -> str:
        if not isinstance(strategy, BaseStrategy):
            raise TypeError("Strategy must inherit from BaseStrategy")
        name = str(strategy.name).strip()
        if not name:
            raise ValueError("Strategy name cannot be empty")
        if name in self._strategies:
            raise ValueError(f"Strategy already registered: {name}")
        self._strategies[name] = strategy
        return name

    def unregister(self, name: str) -> BaseStrategy | None:
        return self._strategies.pop(name, None)

    def list(self) -> List[BaseStrategy]:
        return list(self._strategies.values())

    def matching(self, context: Dict[str, object]) -> List[BaseStrategy]:
        return [strategy for strategy in self._strategies.values() if strategy.matches(context)]

