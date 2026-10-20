from app.voice.recorder import Recorder

recorder = Recorder()

file = recorder.record()

print(file)