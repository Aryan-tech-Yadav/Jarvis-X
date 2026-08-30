"""Audio manager for recording and playback.

Handles:
  - Microphone recording
  - Audio playback
  - Audio format conversion
  - Stream management
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
class AudioConfig:
    """Audio configuration."""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    format: str = "int16"
    duration: float = 5.0


class AudioManager:
    """Manage audio recording and playback.

    Features:
      - Multi-backend recording (sounddevice, speech_recognition, pyaudio)
      - Automatic format conversion
      - Stream management
      - Device selection
    """

    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self._recording = False
        self._backend = self._select_backend()
        self._stream = None

    def _select_backend(self) -> str:
        """Select best available audio backend."""
        try:
            import sounddevice as sd  # noqa: F401
            return "sounddevice"
        except ImportError:
            pass

        try:
            import speech_recognition as sr  # noqa: F401
            return "speech_recognition"
        except ImportError:
            pass

        try:
            import pyaudio  # noqa: F401
            return "pyaudio"
        except ImportError:
            pass

        return "fallback"

    def record(self, duration: float = None, callback: Callable = None) -> Optional[str]:
        """Record audio from microphone.

        Args:
            duration: Recording duration in seconds
            callback: Optional callback for audio chunks

        Returns:
            Path to recorded audio file or None
        """
        duration = duration or self.config.duration
        self._recording = True

        if self._backend == "sounddevice":
            return self._record_sounddevice(duration, callback)
        elif self._backend == "speech_recognition":
            return self._record_speech_recognition(duration)
        elif self._backend == "pyaudio":
            return self._record_pyaudio(duration, callback)
        else:
            return None

    def stop_recording(self):
        """Stop current recording."""
        self._recording = False

    def play(self, audio_path: str, blocking: bool = True):
        """Play audio file.

        Args:
            audio_path: Path to audio file
            blocking: Wait for playback to complete
        """
        if blocking:
            self._play_blocking(audio_path)
        else:
            thread = threading.Thread(target=self._play_blocking, args=(audio_path,))
            thread.start()

    def _play_blocking(self, audio_path: str):
        """Play audio file (blocking)."""
        try:
            system = platform.system()
            if system == "Windows":
                os.system(f'start /min "" "{audio_path}"')
            elif system == "Darwin":
                os.system(f'afplay "{audio_path}"')
            else:
                os.system(f'ffplay -nodisp -autoexit "{audio_path}" 2>/dev/null || aplay "{audio_path}" 2>/dev/null')
        except Exception as exc:
            print(f"[Audio] Playback error: {exc}")

    def _record_sounddevice(self, duration: float, callback: Callable = None) -> Optional[str]:
        """Record using sounddevice."""
        try:
            import sounddevice as sd
            from scipy.io.wavfile import write

            output_path = os.path.join(tempfile.gettempdir(), "jarvis_audio.wav")
            audio = sd.rec(
                int(duration * self.config.sample_rate),
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype="int16",
            )
            sd.wait()

            if not self._recording:
                return None

            write(output_path, self.config.sample_rate, audio)
            return output_path

        except Exception as exc:
            print(f"[Audio] sounddevice error: {exc}")
            return self._record_speech_recognition(duration)

    def _record_speech_recognition(self, duration: float) -> Optional[str]:
        """Record using speech_recognition."""
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            microphone = sr.Microphone()

            with microphone as source:
                print("\nListening...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=int(duration), phrase_time_limit=int(duration))

            output_path = os.path.join(tempfile.gettempdir(), "jarvis_audio.wav")
            with open(output_path, "wb") as f:
                f.write(audio.get_wav_data())

            return output_path

        except Exception as exc:
            print(f"[Audio] speech_recognition error: {exc}")
            return None

    def _record_pyaudio(self, duration: float, callback: Callable = None) -> Optional[str]:
        """Record using pyaudio."""
        try:
            import pyaudio
            import wave

            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=True,
                frames_per_buffer=self.config.chunk_size,
            )

            frames = []
            for _ in range(0, int(self.config.sample_rate / self.config.chunk_size * duration)):
                if not self._recording:
                    break
                data = stream.read(self.config.chunk_size)
                frames.append(data)
                if callback:
                    callback(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            output_path = os.path.join(tempfile.gettempdir(), "jarvis_audio.wav")
            wf = wave.open(output_path, "wb")
            wf.setnchannels(self.config.channels)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.config.sample_rate)
            wf.writeframes(b"".join(frames))
            wf.close()

            return output_path

        except Exception as exc:
            print(f"[Audio] pyaudio error: {exc}")
            return None
