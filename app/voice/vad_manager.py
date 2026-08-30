"""Voice Activity Detection (VAD) manager.

Detects when user is speaking vs silence.
Uses Silero VAD or WebRTC VAD with fallback.
"""

from __future__ import annotations

import os
import time
import tempfile
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class VADResult:
    """Result of VAD analysis."""
    is_speech: bool
    confidence: float
    start_time: float
    end_time: float


class VADManager:
    """Voice Activity Detection manager.

    Engines:
      1. Silero VAD - Best accuracy, lightweight
      2. WebRTC VAD - Good for real-time
      3. Energy-based - Simple fallback
    """

    def __init__(self, threshold: float = 0.5, sample_rate: int = 16000):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self._engine = self._select_engine()
        self._model = None
        if self._engine == "silero":
            self._init_silero()
        elif self._engine == "webrtc":
            self._init_webrtc()

    def _select_engine(self) -> str:
        """Select best available VAD engine."""
        try:
            import torch  # noqa: F401
            return "silero"
        except ImportError:
            pass

        try:
            import webrtcvad  # noqa: F401
            return "webrtc"
        except ImportError:
            pass

        return "energy"

    def _init_silero(self):
        """Initialize Silero VAD model."""
        try:
            import torch
            self._model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )
            print("[VAD] Silero VAD initialized")
        except Exception as exc:
            print(f"[VAD] Silero init failed: {exc}")
            self._engine = "energy"

    def _init_webrtc(self):
        """Initialize WebRTC VAD."""
        try:
            import webrtcvad
            self._vad = webrtcvad.Vad(self._get_webrtc_mode())
            print("[VAD] WebRTC VAD initialized")
        except Exception as exc:
            print(f"[VAD] WebRTC init failed: {exc}")
            self._engine = "energy"

    def _get_webrtc_mode(self) -> int:
        """Get WebRTC VAD mode based on threshold."""
        if self.threshold >= 0.7:
            return 3  # Aggressive
        elif self.threshold >= 0.5:
            return 2  # Medium
        else:
            return 1  # Less aggressive

    def is_speech(self, audio_data: bytes, sample_rate: int = None) -> VADResult:
        """Detect if audio contains speech.

        Args:
            audio_data: Raw audio bytes
            sample_rate: Sample rate (default: 16000)

        Returns:
            VADResult with speech detection
        """
        sample_rate = sample_rate or self.sample_rate
        start_time = time.time()

        if self._engine == "silero":
            result = self._silero_vad(audio_data, sample_rate)
        elif self._engine == "webrtc":
            result = self._webrtc_vad(audio_data, sample_rate)
        else:
            result = self._energy_vad(audio_data)

        return VADResult(
            is_speech=result,
            confidence=0.8 if result else 0.2,
            start_time=start_time,
            end_time=time.time(),
        )

    def _silero_vad(self, audio_data: bytes, sample_rate: int) -> bool:
        """Silero VAD detection."""
        try:
            import torch
            import numpy as np

            audio = np.frombuffer(audio_data, dtype=np.int16)
            audio = audio.astype(np.float32) / 32768.0
            audio_tensor = torch.from_numpy(audio)

            with torch.no_grad():
                speech_prob = self._model(audio_tensor, self.sample_rate).item()

            return speech_prob > self.threshold
        except Exception:
            return self._energy_vad(audio_data)

    def _webrtc_vad(self, audio_data: bytes, sample_rate: int) -> bool:
        """WebRTC VAD detection."""
        try:
            import webrtcvad

            # WebRTC requires specific frame sizes
            frame_duration = 30  # ms
            frame_size = int(sample_rate * frame_duration / 1000 * 2)  # 16-bit = 2 bytes

            if len(audio_data) < frame_size:
                return False

            # Pad audio to frame size
            padded = audio_data[:frame_size] + b'\x00' * (frame_size - len(audio_data))
            return self._vad.is_speech(padded, sample_rate)
        except Exception:
            return self._energy_vad(audio_data)

    def _energy_vad(self, audio_data: bytes) -> bool:
        """Simple energy-based VAD fallback."""
        if not audio_data:
            return False

        # Calculate RMS energy
        samples = len(audio_data) // 2
        if samples == 0:
            return False

        # Convert bytes to samples
        import struct
        fmt = f"{samples}h"
        try:
            audio_samples = struct.unpack(fmt, audio_data[:samples * 2])
        except Exception:
            return False

        # Calculate RMS
        sum_squares = sum(s * s for s in audio_samples)
        rms = (sum_squares / samples) ** 0.5 if samples > 0 else 0

        # Normalize RMS (16-bit audio max is 32768)
        normalized_rms = rms / 32768.0

        return normalized_rms > self.threshold * 0.1

    def detect_speech_segments(self, audio_data: bytes, sample_rate: int = None) -> List[VADResult]:
        """Detect multiple speech segments in audio.

        Returns:
            List of VADResult for each segment
        """
        # Simplified: return single segment for now
        result = self.is_speech(audio_data, sample_rate)
        return [result] if result.is_speech else []
