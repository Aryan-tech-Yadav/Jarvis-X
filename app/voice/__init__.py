"""Voice package - Professional voice system architecture.

Components:
  - AudioManager: Recording and playback
  - WakeWordManager: Always-listening wake word detection
  - VADManager: Voice activity detection
  - STTManager: Speech-to-text with streaming
  - TTSManager: Text-to-speech with interruption
  - StateManager: Conversation state machine
  - VoiceSessionManager: Main session orchestrator
  - JarvisVoice: Legacy compatibility wrapper
"""

from app.voice.audio_manager import AudioManager, AudioConfig
from app.voice.wake_word_manager import WakeWordManager
from app.voice.vad_manager import VADManager, VADResult
from app.voice.stt_manager import STTManager
from app.voice.tts_manager import TTSManager, TTSChunk
from app.voice.state_manager import VoiceState, VoiceStateManager
from app.voice.voice_session_manager import VoiceSessionManager, VoiceSession
from app.voice.jarvis_voice import JarvisVoice
from app.voice.voice_manager import VoiceManager

__all__ = [
    "AudioManager",
    "AudioConfig",
    "WakeWordManager",
    "VADManager",
    "VADResult",
    "STTManager",
    "TTSManager",
    "TTSChunk",
    "VoiceState",
    "VoiceStateManager",
    "VoiceSessionManager",
    "VoiceSession",
    "JarvisVoice",
    "VoiceManager",
]
