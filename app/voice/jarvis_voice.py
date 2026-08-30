"""Enhanced Jarvis voice system with professional architecture.

Legacy wrapper around VoiceSessionManager for backward compatibility.
"""

from __future__ import annotations

import os
import time
import threading
from typing import Optional, Callable

from app.core.logger import Logger
from app.voice.voice_session_manager import VoiceSessionManager


class JarvisVoice:
    """Enhanced voice system for Jarvis-X.

    Professional architecture:
      - WakeWordManager: Always-listening wake word detection
      - VADManager: Voice activity detection
      - STTManager: Speech-to-text with streaming
      - TTSManager: Text-to-speech with interruption
      - StateManager: Conversation state machine
      - VoiceSessionManager: Session orchestrator

    Backward compatible with old API.
    """

    def __init__(self):
        self._listening = False
        self._wake_word = "jarvis"
        self._on_wake: Optional[Callable] = None
        self._on_command: Optional[Callable] = None
        self._session_manager: Optional[VoiceSessionManager] = None
        self._available = False
        self._init_voice()

    def _init_voice(self):
        """Initialize professional voice system."""
        try:
            self._session_manager = VoiceSessionManager(wake_word=self._wake_word)

            # Wire callbacks
            if self._on_wake:
                self._session_manager.wake_word_manager.set_callback(self._on_wake)
            if self._on_command:
                self._session_manager.set_callbacks(
                    on_transcript=self._on_command,
                    on_response=self._on_command,
                )

            self._available = self._session_manager.is_available()
            if self._available:
                Logger.success("[JarvisVoice] Professional voice system initialized")
            else:
                Logger.warning("[JarvisVoice] Voice system in fallback mode")

        except Exception as exc:
            Logger.warning(f"[JarvisVoice] Init failed: {exc}")
            self._session_manager = None
            self._available = False

    def set_wake_callback(self, callback: Callable[[str], None]):
        """Set callback for wake word detection."""
        self._on_wake = callback
        if self._session_manager:
            self._session_manager.wake_word_manager.set_callback(callback)

    def set_command_callback(self, callback: Callable[[str], None]):
        """Set callback for command recognition."""
        self._on_command = callback
        if self._session_manager:
            self._session_manager.set_callbacks(on_transcript=callback, on_response=callback)

    def speak(self, text: str, interrupt: bool = True):
        """Speak text using professional TTS with interruption support.

        Args:
            text: Text to speak
            interrupt: Interrupt current speech if playing
        """
        if not text:
            return

        print(f"Jarvis: {text}")

        if self._session_manager:
            try:
                self._session_manager.speak_response(text, interrupt=interrupt)
                return
            except Exception as exc:
                Logger.warning(f"[JarvisVoice] Speech error: {exc}")

        self._fallback_speak(text)

    def listen(self, timeout: Optional[float] = None) -> Optional[str]:
        """Listen for voice input.

        Args:
            timeout: Maximum listen time in seconds

        Returns:
            Transcribed text or None
        """
        if not self._session_manager:
            Logger.warning("[JarvisVoice] Voice system not available")
            return None

        try:
            return self._session_manager.process_voice_input(timeout=timeout or 10.0)
        except Exception as exc:
            Logger.error(f"[JarvisVoice] Listen error: {exc}")
            return None

    def listen_for_wake_word(self, timeout: Optional[float] = None) -> bool:
        """Listen continuously for wake word.

        Args:
            timeout: Optional timeout

        Returns:
            True if wake word detected
        """
        if not self._session_manager:
            Logger.warning("[JarvisVoice] Wake word not available")
            return False

        try:
            # For compatibility, use background listening
            self.start_wake_word_listening()
            return True
        except Exception as exc:
            Logger.error(f"[JarvisVoice] Wake word error: {exc}")
            return False

    def start_wake_word_listening(self):
        """Start wake word detection in background thread."""
        if not self._session_manager:
            return None

        self._listening = True
        return self._session_manager.start_background_listening()

    def stop_wake_word_listening(self):
        """Stop wake word detection."""
        self._listening = False
        if self._session_manager:
            try:
                self._session_manager.stop_background_listening()
            except Exception:
                pass

    def interrupt(self):
        """Interrupt current speech (barge-in)."""
        if self._session_manager:
            try:
                self._session_manager.interrupt_speech()
            except Exception:
                pass

    def _fallback_speak(self, text: str):
        """Fallback TTS using system commands."""
        try:
            system = platform.system()
            if system == "Windows":
                import win32com.client  # type: ignore
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
            elif system == "Darwin":
                os.system(f'say "{text}"')
            else:
                os.system(f'espeak "{text}" 2>/dev/null')
        except Exception:
            pass

    def set_voice_speed(self, rate: int):
        """Set TTS speed."""
        if self._session_manager:
            try:
                self._session_manager.tts_manager.set_rate(rate)
            except Exception:
                pass

    def set_voice_volume(self, volume: float):
        """Set TTS volume (0.0 to 1.0)."""
        if self._session_manager:
            try:
                self._session_manager.tts_manager.set_volume(volume)
            except Exception:
                pass

    def is_available(self) -> bool:
        """Check if voice system is available."""
        return self._available

    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        if self._session_manager:
            return self._session_manager.is_speaking()
        return False

    def is_listening(self) -> bool:
        """Check if currently listening."""
        if self._session_manager:
            return self._session_manager.is_listening()
        return False
