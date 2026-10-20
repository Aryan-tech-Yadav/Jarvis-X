"""Minimal policy boundary for dispatch authorization."""

from typing import Iterable, Set


class PermissionPolicy:
    def __init__(self, allowed: Iterable[str] = ()):
        self.allowed: Set[str] = set(allowed)

    def allows(self, action: str) -> bool:
        return not self.allowed or action in self.allowed

