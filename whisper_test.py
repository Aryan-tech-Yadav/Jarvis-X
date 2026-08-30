from faster_whisper import WhisperModel
import time

print("Start")

t1 = time.time()

model = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8"
)

print("Loaded in", time.time() - t1, "seconds")