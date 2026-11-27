"""Encurta pausas longas da narração e gera o mapa de tempos (original -> novo).
Uso: tighten_audio.py entrada.wav saida.wav mapa.json"""
import sys, json, wave, numpy as np
src, out, mp = sys.argv[1:4]
MAXP, KEEP, LEAD, TAIL, THR = 0.35, 0.25, 0.15, 0.4, -45.0
w = wave.open(src); sr = w.getframerate(); ch = w.getnchannels()
a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, ch).astype(np.float32)
mono = a.mean(1) / 32768; hop = int(sr * 0.02)
db = np.array([20 * np.log10(np.sqrt(np.mean(mono[i:i + hop] ** 2)) + 1e-7) for i in range(0, len(mono) - hop, hop)])
v = db > THR; idx = np.where(v)[0]; first, last = idx[0] * 0.02, (idx[-1] + 1) * 0.02
# silêncios internos
sil = []; i = idx[0]
while i <= idx[-1]:
    if not v[i]:
        j = i
        while j <= idx[-1] and not v[j]: j += 1
        if (j - i) * 0.02 > MAXP: sil.append((i * 0.02, j * 0.02))
        i = j
    else: i += 1
keep = []; cur = max(first - LEAD, 0)
for s0, s1 in sil:
    keep.append((cur, s0 + KEEP / 2)); cur = s1 - KEEP / 2
keep.append((cur, min(last + TAIL, len(mono) / sr)))
pieces = []; m = []; t = 0.0; f = int(0.012 * sr)
for k0, k1 in keep:
    seg = a[int(k0 * sr):int(k1 * sr)].copy(); r = np.linspace(0, 1, f)[:, None]; seg[:f] *= r; seg[-f:] *= r[::-1]
    pieces.append(seg); m.append([round(k0, 3), round(k1, 3), round(t, 3)]); t += len(seg) / sr
y = np.concatenate(pieces).clip(-32768, 32767).astype(np.int16)
o = wave.open(out, "wb"); o.setnchannels(ch); o.setsampwidth(2); o.setframerate(sr); o.writeframes(y.tobytes()); o.close()
json.dump(m, open(mp, "w")); print(f"{len(sil)} pausas encurtadas · {len(mono)/sr:.2f}s -> {t:.2f}s")
for s0, s1 in sil: print(f"  pausa {s0:.2f}-{s1:.2f} ({s1-s0:.2f}s)")
