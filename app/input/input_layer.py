"""Input Layer - Unified interface for all input types.

Layer 1 of the 5-layer AI Agent architecture.
Normalizes text, voice, and image inputs into a common format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class InputType(Enum):
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"


@dataclass
class InputPayload:
    """Normalized input from any source."""
    raw: Any
    input_type: InputType
    text: str = ""
    language: str = "english"
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    source: str = "unknown"


class InputLayer:
    """Unified input processing layer.

    Accepts raw inputs from text, voice, or image,
    normalizes them, and produces a standardized InputPayload.
    """

    def __init__(self):
        self._voice_manager = None
        self._vision_manager = None
        self._language_processor = None
        self._wake_word_active = False

    def initialize(self, voice_manager=None, vision_manager=None, language_processor=None):
        """Initialize sub-modules."""
        self._voice_manager = voice_manager
        self._vision_manager = vision_manager
        self._language_processor = language_processor

    def process(self, raw_input: Any, input_type: InputType = InputType.TEXT) -> InputPayload:
        """Process raw input into normalized payload."""
        if input_type == InputType.TEXT:
            return self._process_text(raw_input)
        elif input_type == InputType.VOICE:
            return self._process_voice(raw_input)
        elif input_type == InputType.IMAGE:
            return self._process_image(raw_input)
        else:
            return InputPayload(
                raw=raw_input,
                input_type=input_type,
                text=str(raw_input),
                confidence=0.0,
                source="unknown"
            )

    def _process_text(self, raw_input: str) -> InputPayload:
        """Process text input."""
        text = str(raw_input).strip()
        language = self._detect_language(text)

        return InputPayload(
            raw=raw_input,
            input_type=InputType.TEXT,
            text=text,
            language=language,
            confidence=1.0,
            source="text"
        )

    def _process_voice(self, raw_input: str) -> InputPayload:
        """Process voice input (transcribed text)."""
        text = str(raw_input).strip()
        language = self._detect_language(text)

        return InputPayload(
            raw=raw_input,
            input_type=InputType.VOICE,
            text=text,
            language=language,
            confidence=0.95,
            source="voice",
            metadata={"transcribed": True}
        )

    def _process_image(self, raw_input: Any) -> InputPayload:
        """Process image input (multimodal)."""
        if self._vision_manager:
            try:
                result = self._vision_manager.analyze(raw_input)
                return InputPayload(
                    raw=raw_input,
                    input_type=InputType.IMAGE,
                    text=result.get("description", ""),
                    language="english",
                    confidence=result.get("confidence", 0.8),
                    source="image",
                    metadata=result.get("metadata", {})
                )
            except Exception:
                pass

        return InputPayload(
            raw=raw_input,
            input_type=InputType.IMAGE,
            text="[Image analysis not available]",
            confidence=0.0,
            source="image"
        )

    def _detect_language(self, text: str) -> str:
        """Detect language of text."""
        if self._language_processor:
            try:
                return self._language_processor.detect_language(text)
            except Exception:
                pass

        text_lower = text.lower()
        hindi_words = ["hai", "ka", "ki", "se", "mein", "ko", "par", "aur", "nahi", "kya", "batao", "karo", "banao"]
        hindi_count = sum(1 for w in hindi_words if w in text_lower)
        if hindi_count >= 2:
            return "hinglish" if any(c.isascii() for c in text) else "hindi"
        return "english"

    def set_wake_word_active(self, active: bool):
        """Set wake word listening state."""
        self._wake_word_active = active

    @property
    def is_wake_word_active(self) -> bool:
        return self._wake_word_active
