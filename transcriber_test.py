from app.voice.transcriber import Transcriber

ai = Transcriber()

text = ai.transcribe("data/audio.wav")

print("\n Whisper Output:")

print(text)