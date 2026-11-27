import json,sys
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
import wave,numpy as np
w=wave.open(sys.argv[1]); aud=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
segs,info=m.transcribe(aud,language="pt",word_timestamps=True,vad_filter=True,condition_on_previous_text=False)
out=[]
for s in segs:
    print(f"{s.start:6.2f}-{s.end:6.2f} {s.text}")
    for w in s.words: out.append({"w":w.word.strip(),"s":round(w.start,3),"e":round(w.end,3)})
json.dump(out,open(sys.argv[2],"w"),ensure_ascii=False,indent=0)
