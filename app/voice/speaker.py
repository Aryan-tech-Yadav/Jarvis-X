"""Text-to-speech speaker with multiple fallback implementations.

Priority:
1. pyttsx3 (offline TTS)
2. edge-tts (Microsoft Edge TTS, high quality)
3. gTTS (Google TTS)
4. Windows SAPI (native Windows)
5. System commands (say/espeak)
6. Print fallback
"""

from __future__ import annotations

import os
import platform
import tempfile
from typing import Optional


class Speaker:
    """Text-to-speech with fallback support."""

    def __init__(self):
        self._impl = self._select_implementation()
        self._engine = None
        if self._impl == "pyttsx3":
            self._init_pyttsx3()
        elif self._impl == "edge_tts":
            self._init_edge_tts()
        elif self._impl == "gtts":
            self._init_gtts()

    def _select_implementation(self) -> str:
        """Select best available TTS implementation."""
        try:
            import pyttsx3  # noqa: F401
            return "pyttsx3"
        except ImportError:
            pass

        try:
            import edge_tts  # noqa: F401
            return "edge_tts"
        except ImportError:
            pass

        try:
            from gtts import gTTS  # noqa: F401
            return "gtts"
        except ImportError:
            pass

        return "system"

    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine."""
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 170)
            self._engine.setProperty("volume", 1.0)
            print("[Speaker] pyttsx3 ready")
        except Exception as exc:
            print(f"[Speaker] pyttsx3 init failed: {exc}")
            self._impl = "system"

    def _init_edge_tts(self):
        """Initialize edge-tts."""
        try:
            import edge_tts
            self._edge_tts = edge_tts
            print("[Speaker] edge-tts ready")
        except Exception as exc:
            print(f"[Speaker] edge-tts init failed: {exc}")
            self._impl = "system"

    def _init_gtts(self):
        """Initialize gTTS."""
        try:
            from gtts import gTTS
            self._gtts = gTTS
            print("[Speaker] gTTS ready")
        except Exception as exc:
            print(f"[Speaker] gTTS init failed: {exc}")
            self._impl = "system"

    def speak(self, text: str):
        """Speak text using available TTS."""
        if not text:
            return

        print(f"Jarvis: {text}")

        if self._impl == "pyttsx3":
            self._speak_pyttsx3(text)
        elif self._impl == "edge_tts":
            self._speak_edge_tts(text)
        elif self._impl == "gtts":
            self._speak_gtts(text)
        else:
            self._speak_system(text)

    def _speak_pyttsx3(self, text: str):
        """Speak using pyttsx3."""
        try:
            if not self._engine:
                return
            self._engine.stop()
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as exc:
            print(f"[Speaker] pyttsx3 error: {exc}")
            self._speak_system(text)

    def _speak_edge_tts(self, text: str):
        """Speak using edge-tts (high quality neural voices)."""
        try:
            import asyncio
            import edge_tts

            async def _speak():
                communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
                output_path = os.path.join(tempfile.gettempdir(), "jarvis_speech.mp3")
                await communicate.save(output_path)
                self._play_audio(output_path)

            asyncio.run(_speak())
        except Exception as exc:
            print(f"[Speaker] edge-tts error: {exc}")
            self._speak_system(text)

    def _speak_gtts(self, text: str):
        """Speak using Google TTS."""
        try:
            output_path = os.path.join(tempfile.gettempdir(), "jarvis_speech.mp3")
            tts = self._gtts(text=text, lang="en")
            tts.save(output_path)
            self._play_audio(output_path)
        except Exception as exc:
            print(f"[Speaker] gTTS error: {exc}")
            self._speak_system(text)

    def _speak_system(self, text: str):
        """Fallback: use system TTS commands."""
        try:
            system = platform.system()
            if system == "Windows":
                self._speak_windows_sapi(text)
            elif system == "Darwin":
                os.system(f'say "{text}"')
            else:
                os.system(f'espeak "{text}" 2>/dev/null')
        except Exception:
            pass

    def _speak_windows_sapi(self, text: str):
        """Use Windows SAPI for TTS."""
        try:
            import win32com.client  # type: ignore
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak(text)
        except ImportError:
            try:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, None, "powershell", f'-Command "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak(\'{text}\')"', None, 0)
            except Exception:
                pass
        except Exception:
            pass

    def _play_audio(self, file_path: str):
        """Play audio file using system player."""
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

    def set_speed(self, rate: int):
        """Set TTS speed."""
        if self._impl == "pyttsx3" and self._engine:
            self._engine.setProperty("rate", rate)

    def set_volume(self, volume: float):
        """Set TTS volume (0.0 to 1.0)."""
        if self._impl == "pyttsx3" and self._engine:
            self._engine.setProperty("volume", max(0.0, min(1.0, volume)))
