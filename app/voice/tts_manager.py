"""Text-to-Speech (TTS) manager with streaming and interruption.

Supports multiple TTS engines:
  - pyttsx3 (offline)
  - edge-tts (Microsoft, high quality)
  - gTTS (Google)
  - Piper (offline, fast)
  - ElevenLabs (cloud, premium)
"""

from __future__ import annotations

import os
import platform
import tempfile
import time
import threading
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass


@dataclass
class TTSChunk:
    """A chunk of synthesized speech."""
    text: str
    audio_path: str
    duration: float
    is_last: bool = False


class TTSManager:
    """Text-to-Speech manager with streaming and interruption support.

    Features:
      - Multiple engine fallback
      - Streaming synthesis
      - Barge-in / interruption support
      - Audio playback management
    """

    def __init__(self, voice: str = "en-US-GuyNeural", rate: int = 170, volume: float = 1.0):
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self._engine = self._select_engine()
        self._speaker = None
        self._playing = False
        self._interrupted = False
        self._play_thread: Optional[threading.Thread] = None
        self._on_start: Optional[Callable] = None
        self._on_end: Optional[Callable] = None
        self._on_chunk: Optional[Callable] = None

        if self._engine == "pyttsx3":
            self._init_pyttsx3()
        elif self._engine == "edge_tts":
            self._init_edge_tts()
        elif self._engine == "piper":
            self._init_piper()
        elif self._engine == "gtts":
            self._init_gtts()

    def _select_engine(self) -> str:
        """Select best available TTS engine."""
        try:
            import edge_tts  # noqa: F401
            return "edge_tts"
        except ImportError:
            pass

        try:
            import pyttsx3  # noqa: F401
            return "pyttsx3"
        except ImportError:
            pass

        try:
            from gtts import gTTS  # noqa: F401
            return "gtts"
        except ImportError:
            pass

        try:
            import piper  # noqa: F401
            return "piper"
        except ImportError:
            pass

        return "system"

    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine."""
        try:
            import pyttsx3
            self._speaker = pyttsx3.init()
            self._speaker.setProperty("rate", self.rate)
            self._speaker.setProperty("volume", self.volume)
            print("[TTS] pyttsx3 ready")
        except Exception as exc:
            print(f"[TTS] pyttsx3 init failed: {exc}")
            self._engine = "system"

    def _init_edge_tts(self):
        """Initialize edge-tts."""
        try:
            import edge_tts
            self._edge_tts = edge_tts
            print("[TTS] edge-tts ready")
        except Exception as exc:
            print(f"[TTS] edge-tts init failed: {exc}")
            self._engine = "system"

    def _init_piper(self):
        """Initialize Piper TTS."""
        try:
            import piper
            self._piper = piper
            print("[TTS] Piper ready")
        except Exception as exc:
            print(f"[TTS] Piper init failed: {exc}")
            self._engine = "system"

    def _init_gtts(self):
        """Initialize Google TTS."""
        try:
            from gtts import gTTS
            self._gtts = gTTS
            print("[TTS] gTTS ready")
        except Exception as exc:
            print(f"[TTS] gTTS init failed: {exc}")
            self._engine = "system"

    def speak(self, text: str, interrupt: bool = True):
        """Speak text with interruption support.

        Args:
            text: Text to speak
            interrupt: Interrupt current speech if speaking
        """
        if not text:
            return

        if interrupt and self._playing:
            self.interrupt()

        self._playing = True
        self._interrupted = False

        if self._on_start:
            try:
                self._on_start(text)
            except Exception:
                pass

        try:
            if self._engine == "edge_tts":
                self._speak_edge_tts(text)
            elif self._engine == "pyttsx3":
                self._speak_pyttsx3(text)
            elif self._engine == "gtts":
                self._speak_gtts(text)
            else:
                self._speak_system(text)
        except Exception as exc:
            print(f"[TTS] Speech error: {exc}")
        finally:
            self._playing = False
            if self._on_end:
                try:
                    self._on_end()
                except Exception:
                    pass

    def speak_streaming(self, text_generator, chunk_size: int = 50):
        """Speak text as it streams in.

        Args:
            text_generator: Generator yielding text chunks
            chunk_size: Characters per chunk
        """
        buffer = ""
        for chunk in text_generator:
            if self._interrupted:
                break

            buffer += chunk
            if len(buffer) >= chunk_size:
                self.speak(buffer, interrupt=False)
                buffer = ""

        if buffer and not self._interrupted:
            self.speak(buffer, interrupt=False)

    def interrupt(self):
        """Interrupt current speech (barge-in)."""
        self._interrupted = True
        self._playing = False

        if self._engine == "pyttsx3" and self._speaker:
            try:
                self._speaker.stop()
            except Exception:
                pass

    def is_playing(self) -> bool:
        """Check if currently speaking."""
        return self._playing

    def set_voice(self, voice: str):
        """Set TTS voice."""
        self.voice = voice
        if self._engine == "pyttsx3" and self._speaker:
            try:
                self._speaker.setProperty("voice", voice)
            except Exception:
                pass

    def set_rate(self, rate: int):
        """Set speech rate."""
        self.rate = rate
        if self._engine == "pyttsx3" and self._speaker:
            try:
                self._speaker.setProperty("rate", rate)
            except Exception:
                pass

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        if self._engine == "pyttsx3" and self._speaker:
            try:
                self._speaker.setProperty("volume", self.volume)
            except Exception:
                pass

    def _speak_edge_tts(self, text: str):
        """Speak using edge-tts."""
        try:
            import asyncio
            import edge_tts

            async def _speak():
                communicate = edge_tts.Communicate(text, self.voice)
                output_path = os.path.join(tempfile.gettempdir(), "jarvis_speech.mp3")
                await communicate.save(output_path)
                self._play_audio(output_path)

            asyncio.run(_speak())
        except Exception as exc:
            print(f"[TTS] edge-tts error: {exc}")
            self._speak_system(text)

    def _speak_pyttsx3(self, text: str):
        """Speak using pyttsx3."""
        try:
            if not self._speaker:
                return
            self._speaker.stop()
            self._speaker.say(text)
            self._speaker.runAndWait()
        except Exception as exc:
            print(f"[TTS] pyttsx3 error: {exc}")
            self._speak_system(text)

    def _speak_gtts(self, text: str):
        """Speak using Google TTS."""
        try:
            output_path = os.path.join(tempfile.gettempdir(), "jarvis_speech.mp3")
            tts = self._gtts(text=text, lang="en")
            tts.save(output_path)
            self._play_audio(output_path)
        except Exception as exc:
            print(f"[TTS] gTTS error: {exc}")
            self._speak_system(text)

    def _speak_system(self, text: str):
        """Fallback system TTS."""
        try:
            system = platform.system()
            if system == "Windows":
                self._speak_windows(text)
            elif system == "Darwin":
                os.system(f'say "{text}"')
            else:
                os.system(f'espeak "{text}" 2>/dev/null')
        except Exception:
            pass

    def _speak_windows(self, text: str):
        """Windows TTS fallback."""
        try:
            import win32com.client  # type: ignore
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(text)
        except ImportError:
            try:
                safe_text = text.replace("'", "''")
                cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak(\'{safe_text}\')"'
                os.system(cmd)
            except Exception:
                pass

    def _play_audio(self, file_path: str):
        """Play audio file."""
        try:
            system = platform.system()
            if system == "Windows":
                os.system(f'start /min "" "{file_path}"')
            elif system == "Darwin":
                os.system(f'afplay "{file_path}"')
            else:
                os.system(f'ffplay -nodisp -autoexit "{file_path}" 2>/dev/null || aplay "{file_path}" 2>/dev/null')
        except Exception:
            pass
