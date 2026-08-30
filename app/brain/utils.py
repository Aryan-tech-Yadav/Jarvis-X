"""Shared utilities for brain modules.

Eliminates code duplication across:
  - _emit() helper
  - _extract_json() helper
  - Common validation
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional


def emit_event(event_bus, event_type: str, payload: Dict[str, Any]):
    """Emit event through event bus with error handling.

    Replaces duplicated _emit() methods across 7+ brain modules.
    """
    if event_bus:
        try:
            event_bus.publish(event_type, payload)
        except Exception:
            pass


def extract_json(text: str) -> Optional[str]:
    """Extract JSON array from text.

    Replaces duplicated _extract_json() methods.
    """
    json_match = re.search(r"\[.*\]", text, re.DOTALL)
    if json_match:
        return json_match.group()
    return None


def validate_non_empty(value: str, name: str = "value") -> bool:
    """Validate that a string is not empty."""
    return bool(value and value.strip())


def validate_dict_keys(data: Dict[str, Any], required_keys: list) -> bool:
    """Validate that dict has all required keys."""
    return all(key in data for key in required_keys)
