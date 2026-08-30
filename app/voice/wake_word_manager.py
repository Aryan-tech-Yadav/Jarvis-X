"""Wake word manager for always-listening voice activation.

Supports multiple wake word engines with fallback:
  - Porcupine (Picovoice)
  - OpenWakeWord
  - SpeechRecognition keyword matching
  - Manual/fallback
"""

from __future__ import annotations

import os
import time
import threading
from typing import Optional, Callable, List, Dict, Any


class WakeWordManager:
    """Manage wake word detection with multiple engine support.

    Engines:
      1. Porcupine - Industry standard, low false positives
      2. OpenWakeWord - Open source, good accuracy
      3. SpeechRecognition - Fallback using keyword matching
      4. Manual - User presses key/button
    """

    def __init__(self, wake_word: str = "jarvis", sensitivity: float = 0.5):
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self._engine = None
        self._listening = False
        self._callback: Optional[Callable] = None
        self._thread: Optional[threading.Thread] = None
        self._init_engine()

    def _init_engine(self):
        """Initialize best available wake word engine."""
        # Try Porcupine first
        try:
            import pvporcupine  # noqa: F401
            self._engine = "porcupine"
            return
        except ImportError:
            pass

        # Try OpenWakeWord
        try:
            import openwakeword  # noqa: F401
            self._engine = "openwakeword"
            return
        except ImportError:
            pass

        # Fallback to speech_recognition keyword matching
        try:
            import speech_recognition as sr  # noqa: F401
            self._engine = "speech_recognition"
            return
        except ImportError:
            pass

        self._engine = "manual"

    def set_callback(self, callback: Callable[[str], None]):
        """Set callback when wake word is detected.

        Args:
            callback: Function receiving detected text
        """
        self._callback = callback

    def start(self, background: bool = True) -> Optional[threading.Thread]:
        """Start wake word detection.

        Args:
            background: Run in background thread

        Returns:
            Thread if background=True, None otherwise
        """
        if self._listening:
            return None

        self._listening = True

        if background:
            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            return self._thread

        self._listen_loop()
        return None

    def stop(self):
        """Stop wake word detection."""
        self._listening = False

    def _listen_loop(self):
        """Main listening loop."""
        if self._engine == "porcupine":
            self._porcupine_loop()
        elif self._engine == "openwakeword":
            self._openwakeword_loop()
        elif self._engine == "speech_recognition":
            self._keyword_loop()
        else:
            self._manual_loop()

    def _porcupine_loop(self):
        """Porcupine wake word detection loop."""
        try:
            import pvporcupine
            import struct
            import sounddevice as sd

            porcupine = pvporcupine.create(keywords=[self.wake_word], sensitivities=[self.sensitivity])

            def audio_callback(indata, frames, time_info, status):
                if not self._listening:
                    return
                pcm = struct.unpack_from("h" * frames, indata.tobytes())
                keyword_index = porcupine.process(pcm)
                if keyword_index >= 0:
                    self._trigger("Porcupine detected wake word")

            with sd.InputStream(samplerate=16000, channels=1, dtype="int16",
                                frames_per_buffer=porcupine.frame_length,
                                callback=audio_callback):
                while self._listening:
                    time.sleep(0.1)

            porcupine.delete()

        except Exception as exc:
            print(f"[WakeWord] Porcupine error: {exc}")
            self._engine = "fallback"
            self._keyword_loop()

    def _openwakeword_loop(self):
        """OpenWakeWord detection loop."""
        try:
            from openwakeword.model import Model
            import numpy as np

            model = Model(wakeword_models=[self.wake_word + ".tflite"] if False else [])
            sample_rate = 16000
            frame_length = 1024

            while self._listening:
                try:
                    import sounddevice as sd
                    audio = sd.rec(frame_length, samplerate=sample_rate, channels=1, dtype="float32")
                    sd.wait()
                    audio = audio.flatten()

                    prediction = model.predict(audio)
                    if prediction and max(prediction.values()) > self.sensitivity:
                        self._trigger("OpenWakeWord detected wake word")
                        time.sleep(1)

                except Exception:
                    time.sleep(0.5)

        except Exception as exc:
            print(f"[WakeWord] OpenWakeWord error: {exc}")
            self._engine = "speech_recognition"
            self._keyword_loop()

    def _keyword_loop(self):
        """Keyword matching fallback using speech recognition."""
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            microphone = sr.Microphone()

            with microphone as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)

            while self._listening:
                try:
                    with microphone as source:
                        audio = recognizer.listen(source, timeout=2, phrase_time_limit=2)
                    text = recognizer.recognize_google(audio).lower()
                    if self.wake_word in text:
                        self._trigger(f"Keyword matched: {text}")
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception:
                    time.sleep(0.5)

        except Exception as exc:
            print(f"[WakeWord] Keyword detection error: {exc}")
            self._manual_loop()

    def _manual_loop(self):
        """Manual fallback - wait for user input."""
        while self._listening:
            try:
                text = input().strip().lower()
                if self.wake_word in text:
                    self._trigger(f"Manual: {text}")
            except Exception:
                time.sleep(0.5)

    def _trigger(self, reason: str):
        """Trigger wake word callback."""
        print(f"[WakeWord] {reason}")
        if self._callback:
            try:
                self._callback(self.wake_word)
            except Exception as exc:
                print(f"[WakeWord] Callback error: {exc}")
