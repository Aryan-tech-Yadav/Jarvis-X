"""Voice manager - unified interface for voice operations.

Provides fallback support when voice components are unavailable.
"""

from __future__ import annotations

from typing import Optional

from app.core.logger import Logger


class VoiceManager:
    """Unified voice interface with graceful fallbacks.

    Wraps Recorder, Transcriber, and Speaker with fallback support.
    Falls back to text input/output when voice is unavailable.
    """

    def __init__(self):
        self.recorder = None
        self.transcriber = None
        self.speaker = None
        self._available = False
        self._init_components()

    def _init_components(self):
        """Initialize voice components with fallbacks."""
        try:
            from app.voice.recorder import Recorder
            self.recorder = Recorder()
        except Exception as exc:
            Logger.warning(f"[VoiceManager] Recorder init failed: {exc}")

        try:
            from app.voice.transcriber import Transcriber
            self.transcriber = Transcriber()
        except Exception as exc:
            Logger.warning(f"[VoiceManager] Transcriber init failed: {exc}")

        try:
            from app.voice.speaker import Speaker
            self.speaker = Speaker()
        except Exception as exc:
            Logger.warning(f"[VoiceManager] Speaker init failed: {exc}")

        self._available = self.recorder is not None or self.speaker is not None
        if self._available:
            Logger.success("[VoiceManager] Voice system initialized")
        else:
            Logger.warning("[VoiceManager] Voice system unavailable - using text fallback")

    def listen(self, timeout: Optional[float] = None) -> Optional[str]:
        """Listen for voice input and transcribe.

        Returns:
            Transcribed text or None if unavailable.
        """
        if not self.recorder or not self.transcriber:
            Logger.warning("[VoiceManager] Voice input not available")
            return None

        try:
            audio_path = self.recorder.record(timeout=timeout)
            if not audio_path or not audio_path:
                return None

            text = self.transcriber.transcribe(audio_path)
            if text:
                print(f"Recognized: {text}")
            return text.strip() if text else None

        except Exception as exc:
            Logger.error(f"[VoiceManager] Listen error: {exc}")
            return None

    def speak(self, text: str):
        """Speak text using available TTS.

        Always prints text as fallback.
        """
        if not text:
            return

        if self.speaker:
            try:
                self.speaker.speak(text)
                return
            except Exception as exc:
                Logger.warning(f"[VoiceManager] Speech error: {exc}")

        # Final fallback: print
        print(f"Jarvis: {text}")

    def is_available(self) -> bool:
        """Check if voice system is available."""
        return self._available
