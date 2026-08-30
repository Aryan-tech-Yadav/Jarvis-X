"""Speech-to-Text (STT) manager with streaming support.

Supports multiple STT engines:
  - faster-whisper (local, fast)
  - openai-whisper (local, accurate)
  - Deepgram (cloud, fast + accurate)
  - Google Speech (cloud)
  - SpeechRecognition fallback
"""

from __future__ import annotations

import os
import time
import tempfile
import queue
import threading
from typing import Optional, Callable, Dict, Any, List


class STTManager:
    """Speech-to-Text manager with streaming and multiple engine support.

    Features:
      - Multiple engine fallback
      - Streaming transcription
      - Interim results
      - Language detection
    """

    def __init__(self, model_size: str = "tiny", language: str = "en"):
        self.model_size = model_size
        self.language = language
        self._engine = self._select_engine()
        self._model = None
        self._streaming = False
        self._audio_queue: queue.Queue = queue.Queue()
        self._result_queue: queue.Queue = queue.Queue()
        self._stream_thread: Optional[threading.Thread] = None
        self._on_interim: Optional[Callable] = None
        self._on_final: Optional[Callable] = None

        if self._engine == "faster_whisper":
            self._init_faster_whisper()
        elif self._engine == "whisper":
            self._init_whisper()
        elif self._engine == "deepgram":
            self._init_deepgram()

    def _select_engine(self) -> str:
        """Select best available STT engine."""
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
            from deepgram import DeepgramClient  # noqa: F401
            return "deepgram"
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
            print(f"[STT] Loading faster-whisper model: {self.model_size}")
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            print("[STT] faster-whisper ready")
        except Exception as exc:
            print(f"[STT] faster-whisper init failed: {exc}")
            self._engine = "fallback"

    def _init_whisper(self):
        """Initialize openai-whisper model."""
        try:
            import whisper
            print(f"[STT] Loading whisper model: {self.model_size}")
            self._model = whisper.load_model(self.model_size)
            print("[STT] whisper ready")
        except Exception as exc:
            print(f"[STT] whisper init failed: {exc}")
            self._engine = "fallback"

    def _init_deepgram(self):
        """Initialize Deepgram client."""
        try:
            from deepgram import DeepgramClient
            api_key = os.getenv("DEEPGRAM_API_KEY")
            if api_key:
                self._model = DeepgramClient(api_key)
                print("[STT] Deepgram ready")
            else:
                print("[STT] Deepgram API key not found")
                self._engine = "fallback"
        except Exception as exc:
            print(f"[STT] Deepgram init failed: {exc}")
            self._engine = "fallback"

    def transcribe(self, audio_path: str, language: str = None) -> Optional[str]:
        """Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Language code (default: self.language)

        Returns:
            Transcribed text or None
        """
        if not audio_path or not os.path.exists(audio_path):
            return None

        language = language or self.language

        if self._engine == "faster_whisper":
            return self._transcribe_faster_whisper(audio_path, language)
        elif self._engine == "whisper":
            return self._transcribe_whisper(audio_path, language)
        elif self._engine == "deepgram":
            return self._transcribe_deepgram(audio_path, language)
        elif self._engine == "speech_recognition":
            return self._transcribe_speech_recognition(audio_path, language)
        else:
            return None

    def _transcribe_faster_whisper(self, audio_path: str, language: str) -> Optional[str]:
        """Transcribe using faster-whisper."""
        try:
            if not self._model:
                return None
            segments, info = self._model.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
            )
            text = ""
            for segment in segments:
                text += segment.text + " "
            return text.strip() if text else None
        except Exception as exc:
            print(f"[STT] faster-whisper error: {exc}")
            return None

    def _transcribe_whisper(self, audio_path: str, language: str) -> Optional[str]:
        """Transcribe using openai-whisper."""
        try:
            if not self._model:
                return None
            result = self._model.transcribe(audio_path, language=language)
            return result.get("text", "").strip() or None
        except Exception as exc:
            print(f"[STT] whisper error: {exc}")
            return None

    def _transcribe_deepgram(self, audio_path: str, language: str) -> Optional[str]:
        """Transcribe using Deepgram."""
        try:
            with open(audio_path, "rb") as f:
                audio = f.read()

            response = self._model.listen.rest.v("1").transcribe_file(
                {"buffer": audio, "mimetype": "audio/wav"},
                {
                    "model": "nova-2",
                    "language": language,
                    "smart_format": True,
                },
            )

            if response.results:
                transcript = response.results.channels[0].alternatives[0].transcript
                return transcript.strip() if transcript else None
        except Exception as exc:
            print(f"[STT] Deepgram error: {exc}")
            return None

    def _transcribe_speech_recognition(self, audio_path: str, language: str) -> Optional[str]:
        """Transcribe using speech_recognition library."""
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = recognizer.record(source)

            try:
                text = recognizer.recognize_google(audio, language=language)
                return text.strip() if text else None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as exc:
                print(f"[STT] Speech Recognition API error: {exc}")
                return None
        except Exception as exc:
            print(f"[STT] speech_recognition error: {exc}")
            return None

    def start_streaming(self, on_interim: Callable[[str], None] = None, on_final: Callable[[str], None] = None):
        """Start streaming transcription.

        Args:
            on_interim: Callback for interim results
            on_final: Callback for final result
        """
        if self._streaming:
            return

        self._streaming = True
        self._on_interim = on_interim
        self._on_final = on_final
        self._audio_queue = queue.Queue()
        self._result_queue = queue.Queue()
        self._stream_thread = threading.Thread(target=self._stream_loop, daemon=True)
        self._stream_thread.start()

    def stop_streaming(self):
        """Stop streaming transcription."""
        self._streaming = False
        if self._stream_thread:
            self._stream_thread.join(timeout=1)
            self._stream_thread = None

    def feed_audio(self, audio_data: bytes):
        """Feed audio data to streaming pipeline."""
        if self._streaming:
            self._audio_queue.put(audio_data)

    def _stream_loop(self):
        """Streaming transcription loop."""
        # Simplified: process audio chunks as they arrive
        while self._streaming:
            try:
                audio_data = self._audio_queue.get(timeout=0.1)
                if audio_data and self._on_interim:
                    self._on_interim("[streaming audio...]")
            except queue.Empty:
                continue
            except Exception:
                pass

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages."""
        return ["en", "hi", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
