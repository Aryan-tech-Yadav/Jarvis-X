"""Voice recorder with multiple fallback implementations.

Priority:
1. sounddevice + scipy (native recording)
2. speech_recognition library
3. pyaudio
4. Manual input fallback
"""

from __future__ import annotations

import os
import platform
import tempfile
from typing import Optional


class Recorder:
    """Record audio from microphone with fallback support."""

    def __init__(self):
        self.sample_rate = 16000
        self.duration = 5
        self._impl = self._select_implementation()

    def _select_implementation(self) -> str:
        """Select best available recording implementation."""
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

    def record(self, duration: Optional[float] = None) -> Optional[str]:
        """Record audio and return path to saved file."""
        duration = duration or self.duration

        if self._impl == "sounddevice":
            return self._record_sounddevice(duration)
        elif self._impl == "speech_recognition":
            return self._record_speech_recognition(duration)
        elif self._impl == "pyaudio":
            return self._record_pyaudio(duration)
        else:
            return self._record_fallback(duration)

    def _record_sounddevice(self, duration: float) -> Optional[str]:
        """Record using sounddevice + scipy."""
        try:
            import sounddevice as sd
            from scipy.io.wavfile import write

            output_path = os.path.join(tempfile.gettempdir(), "jarvis_audio.wav")
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            write(output_path, self.sample_rate, audio)
            return output_path
        except Exception as exc:
            print(f"[Recorder] sounddevice failed: {exc}")
            return self._record_fallback(duration)

    def _record_speech_recognition(self, duration: float) -> Optional[str]:
        """Record using speech_recognition library."""
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            microphone = sr.Microphone()

            with microphone as source:
                print("\n Listening...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=int(duration), phrase_time_limit=int(duration))

            output_path = os.path.join(tempfile.gettempdir(), "jarvis_audio.wav")
            with open(output_path, "wb") as f:
                f.write(audio.get_wav_data())

            return output_path
        except Exception as exc:
            print(f"[Recorder] speech_recognition failed: {exc}")
            return self._record_fallback(duration)

    def _record_pyaudio(self, duration: float) -> Optional[str]:
        """Record using pyaudio."""
        try:
            import pyaudio
            import wave

            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = self.sample_rate

            p = pyaudio.PyAudio()
            stream = p.open(format=format, channels=channels, rate=rate, input=True, frames_per_buffer=chunk)
            frames = []

            print("\n Listening...")
            for _ in range(0, int(rate / chunk * duration)):
                data = stream.read(chunk)
                frames.append(data)

            stream.stop_stream()
            stream.close()
            p.terminate()

            output_path = os.path.join(tempfile.gettempdir(), "jarvis_audio.wav")
            wf = wave.open(output_path, "wb")
            wf.setnchannels(channels)
            wf.setsampwidth(p.get_sample_size(format))
            wf.setframerate(rate)
            wf.writeframes(b"".join(frames))
            wf.close()

            return output_path
        except Exception as exc:
            print(f"[Recorder] pyaudio failed: {exc}")
            return self._record_fallback(duration)

    def _record_fallback(self, duration: float) -> Optional[str]:
        """Fallback: ask user to type instead of voice."""
        print("\n[Recorder] Voice input not available. Please type your command.")
        return None
