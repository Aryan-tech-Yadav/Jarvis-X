from app.voice.voice_manager import VoiceManager

voice = VoiceManager()

text = voice.listen()

print(text)