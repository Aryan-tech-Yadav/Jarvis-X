"""Speech-to-text transcriber with multiple fallback implementations.

Priority:
1. faster_whisper (fast, local)
2. openai-whisper (local)
3. speech_recognition + Google/Whisper APIs
4. Mock/dummy for testing
"""

from __future__ import annotations

import os
import tempfile
from typing import Optional


class Transcriber:
    """Transcribe audio to text with fallback support."""

    def __init__(self):
        self._impl = self._select_implementation()
        self._model = None
        if self._impl == "faster_whisper":
            self._init_faster_whisper()
        elif self._impl == "whisper":
            self._init_whisper()
        elif self._impl == "speech_recognition":
            self._init_speech_recognition()

    def _select_implementation(self) -> str:
        """Select best available transcription implementation."""
        try:
            import faster_whisper  # noqa: F401
            return "faster_whisper"
        except ImportError:
            pass

        try:
            import whisper  # noqa: F401
            return "whisper"
        except ImportError:
            pass

        try:
            import speech_recognition as sr  # noqa: F401
            return "speech_recognition"
        except ImportError:
            pass

        return "fallback"

    def _init_faster_whisper(self):
        """Initialize faster-whisper model."""
        try:
            from faster_whisper import WhisperModel
            print("[Transcriber] Loading faster-whisper model...")
            self._model = WhisperModel("tiny", device="cpu", compute_type="int8")
            print("[Transcriber] faster-whisper ready")
        except Exception as exc:
            print(f"[Transcriber] faster-whisper init failed: {exc}")
            self._impl = "fallback"

    def _init_whisper(self):
        """Initialize openai-whisper model."""
        try:
            import whisper
            print("[Transcriber] Loading whisper model...")
            self._model = whisper.load_model("tiny")
            print("[Transcriber] whisper ready")
        except Exception as exc:
            print(f"[Transcriber] whisper init failed: {exc}")
            self._impl = "fallback"

    def _init_speech_recognition(self):
        """Initialize speech_recognition recognizer."""
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            print("[Transcriber] speech_recognition ready")
        except Exception as exc:
            print(f"[Transcriber] speech_recognition init failed: {exc}")
            self._impl = "fallback"

    def transcribe(self, audio_path: str) -> Optional[str]:
        """Transcribe audio file to text."""
        if not audio_path or not os.path.exists(audio_path):
            return None

        if self._impl == "faster_whisper":
            return self._transcribe_faster_whisper(audio_path)
        elif self._impl == "whisper":
            return self._transcribe_whisper(audio_path)
        elif self._impl == "speech_recognition":
            return self._transcribe_speech_recognition(audio_path)
        else:
            return self._transcribe_fallback()

    def _transcribe_faster_whisper(self, audio_path: str) -> Optional[str]:
        """Transcribe using faster-whisper."""
        try:
            if not self._model:
                return None
            segments, _ = self._model.transcribe(audio_path)
            text = ""
            for segment in segments:
                text += segment.text + " "
            return text.strip() if text else None
        except Exception as exc:
            print(f"[Transcriber] faster-whisper error: {exc}")
            return None

    def _transcribe_whisper(self, audio_path: str) -> Optional[str]:
        """Transcribe using openai-whisper."""
        try:
            if not self._model:
                return None
            result = self._model.transcribe(audio_path)
            return result.get("text", "").strip() or None
        except Exception as exc:
            print(f"[Transcriber] whisper error: {exc}")
            return None

    def _transcribe_speech_recognition(self, audio_path: str) -> Optional[str]:
        """Transcribe using speech_recognition library."""
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio)
                return text.strip() if text else None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as exc:
                print(f"[Transcriber] Speech Recognition API error: {exc}")
                return None
        except Exception as exc:
            print(f"[Transcriber] speech_recognition error: {exc}")
            return None

    def _transcribe_fallback(self) -> Optional[str]:
        """Fallback: return None (will trigger text input)."""
        print("[Transcriber] No STT engine available. Please type your command.")
        return None
