"""Voice session manager - professional event-driven voice architecture.

Ties together:
  - WakeWordManager
  - AudioManager
  - VADManager
  - STTManager
  - TTSManager
  - StateManager

This is the main entry point for voice interactions.
"""

from __future__ import annotations

import os
import time
import threading
from typing import Optional, Callable, Dict, Any, List
from dataclasses import dataclass, field

from app.core.logger import Logger
from app.voice.state_manager import VoiceState, VoiceStateManager
from app.voice.audio_manager import AudioManager, AudioConfig
from app.voice.wake_word_manager import WakeWordManager
from app.voice.vad_manager import VADManager, VADResult
from app.voice.stt_manager import STTManager
from app.voice.tts_manager import TTSManager


@dataclass
class VoiceSession:
    """Active voice session data."""
    session_id: str
    state: VoiceState
    transcript: str = ""
    response: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0
    end_time: float = 0.0


class VoiceSessionManager:
    """Professional voice session manager.

    Architecture:
      1. WakeWordEngine -> detects "Jarvis"
      2. VAD -> detects speech boundaries
      3. STT -> converts speech to text
      4. AI Brain -> processes intent
      5. Tool Execution -> performs actions
      6. TTS -> converts response to speech

    Features:
      - Event-driven architecture
      - State machine for conversation flow
      - Barge-in / interruption support
      - Streaming STT/TTS
      - Background wake word listening
      - Graceful degradation
    """

    def __init__(
        self,
        wake_word: str = "jarvis",
        stt_model: str = "tiny",
        tts_voice: str = "en-US-GuyNeural",
        sample_rate: int = 16000,
    ):
        self.session_id = self._generate_session_id()
        self._lock = threading.RLock()

        # Initialize components
        self.state_manager = VoiceStateManager()
        self.audio_manager = AudioManager(AudioConfig(sample_rate=sample_rate))
        self.wake_word_manager = WakeWordManager(wake_word=wake_word)
        self.vad_manager = VADManager(sample_rate=sample_rate)
        self.stt_manager = STTManager(model_size=stt_model)
        self.tts_manager = TTSManager(voice=tts_voice)

        # Callbacks
        self._on_transcript: Optional[Callable] = None
        self._on_response: Optional[Callable] = None
        self._on_state_change: Optional[Callable] = None
        self._on_error: Optional[Callable] = None

        # Background listening
        self._wake_word_thread: Optional[threading.Thread] = None
        self._listening = False

        # Setup state listeners
        self._setup_state_listeners()

        # Setup wake word callback
        self.wake_word_manager.set_callback(self._on_wake_word_detected)

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return f"voice_session_{uuid.uuid4().hex[:8]}"

    def _setup_state_listeners(self):
        """Setup state change listeners."""
        self.state_manager.add_listener(VoiceState.LISTENING, self._on_listening_start)
        self.state_manager.add_listener(VoiceState.THINKING, self._on_thinking_start)
        self.state_manager.add_listener(VoiceState.SPEAKING, self._on_speaking_start)
        self.state_manager.add_listener(VoiceState.IDLE, self._on_idle)

    def _on_wake_word_detected(self, text: str):
        """Handle wake word detection."""
        with self._lock:
            self.state_manager.transition("wake_word", {"text": text})

    def _on_listening_start(self, old_state: VoiceState, new_state: VoiceState, trigger: str):
        """Handle listening state start."""
        Logger.info("[VoiceSession] Listening for speech...")

    def _on_thinking_start(self, old_state: VoiceState, new_state: VoiceState, trigger: str):
        """Handle thinking state start."""
        Logger.info("[VoiceSession] Processing speech...")

    def _on_speaking_start(self, old_state: VoiceState, new_state: VoiceState, trigger: str):
        """Handle speaking state start."""
        Logger.info("[VoiceSession] Speaking response...")

    def _on_idle(self, old_state: VoiceState, new_state: VoiceState, trigger: str):
        """Handle idle state."""
        Logger.info("[VoiceSession] Idle")

    def start_background_listening(self) -> bool:
        """Start background wake word detection.

        Returns:
            True if started successfully
        """
        if self._listening:
            return False

        self._listening = True
        self.state_manager.force_state(VoiceState.IDLE)

        self._wake_word_thread = threading.Thread(
            target=self._background_loop,
            daemon=True,
        )
        self._wake_word_thread.start()
        return True

    def stop_background_listening(self):
        """Stop background wake word detection."""
        self._listening = False
        self.wake_word_manager.stop()
        if self._wake_word_thread:
            self._wake_word_thread.join(timeout=1)
            self._wake_word_thread = None

    def _background_loop(self):
        """Background listening loop."""
        while self._listening:
            try:
                # Start wake word detection
                self.wake_word_manager.start(background=False)
            except Exception as exc:
                Logger.error(f"[VoiceSession] Background loop error: {exc}")
                time.sleep(1)

    def process_voice_input(self, timeout: float = 10.0) -> Optional[str]:
        """Process voice input from user.

        Args:
            timeout: Maximum time to wait for input

        Returns:
            Transcribed text or None
        """
        with self._lock:
            self.state_manager.transition("wake_word")

            # Listen for speech
            self.state_manager.transition("recognized")
            self.state_manager.transition("speech_end")

            # Transcribe
            audio_path = self.audio_manager.record(duration=timeout)
            if not audio_path:
                return None

            text = self.stt_manager.transcribe(audio_path)
            if text:
                self.state_manager.transition("speech_end", {"text": text})

            return text

    def speak_response(self, text: str, interrupt: bool = True):
        """Speak response to user.

        Args:
            text: Text to speak
            interrupt: Interrupt current speech
        """
        with self._lock:
            self.state_manager.transition("response_ready")
            self.tts_manager.speak(text, interrupt=interrupt)
            self.state_manager.transition("finished")

    def interrupt_speech(self):
        """Interrupt current speech (barge-in)."""
        self.tts_manager.interrupt()
        with self._lock:
            self.state_manager.transition("interrupted")

    def set_callbacks(
        self,
        on_transcript: Callable = None,
        on_response: Callable = None,
        on_state_change: Callable = None,
        on_error: Callable = None,
    ):
        """Set event callbacks.

        Args:
            on_transcript: Called when speech is transcribed
            on_response: Called when response is ready
            on_state_change: Called on state changes
            on_error: Called on errors
        """
        self._on_transcript = on_transcript
        self._on_response = on_response
        self._on_state_change = on_state_change
        self._on_error = on_error

    def get_session(self) -> VoiceSession:
        """Get current session info."""
        return VoiceSession(
            session_id=self.session_id,
            state=self.state_manager.current_state,
        )

    def is_listening(self) -> bool:
        """Check if currently listening."""
        return self.state_manager.is_listening()

    def is_speaking(self) -> bool:
        """Check if currently speaking."""
        return self.tts_manager.is_playing()

    def is_available(self) -> bool:
        """Check if voice system is available."""
        return (
            self.wake_word_manager is not None
            or self.audio_manager is not None
            or self.stt_manager is not None
            or self.tts_manager is not None
        )
