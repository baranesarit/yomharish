"""Hebrew word-level transcription with ivrit-ai Whisper (faster-whisper, CPU).

usage: transcribe.py VIDEO_OR_AUDIO OUT_WORDS.json
Prints one line per segment with every word and its [start-end] seconds.
"""
import json, os, subprocess, sys, tempfile, wave
import numpy as np

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # xet CAS host is not reachable through the proxy
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
with tempfile.TemporaryDirectory() as td:
    wav = os.path.join(td, "a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-ac", "1", "-ar", "16000", wav], check=True)
    w = wave.open(wav)
    audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768

model = WhisperModel(os.environ.get("ALMA_WHISPER", "ivrit-ai/whisper-large-v3-turbo-ct2"), device="cpu", compute_type="int8", cpu_threads=os.cpu_count())
segs, _ = model.transcribe(audio, language="he", word_timestamps=True, beam_size=5, vad_filter=False)
res = []
for s in segs:
    words = [{"w": x.word, "s": round(x.start, 2), "e": round(x.end, 2)} for x in s.words]
    res.append({"start": s.start, "end": s.end, "text": s.text, "words": words})
    print(" ".join(f"{x['w'].strip()}[{x['s']:.2f}-{x['e']:.2f}]" for x in words), flush=True)
json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
