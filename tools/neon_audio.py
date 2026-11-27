"""Trilha + efeitos sonoros (whoosh/pop/tick) sintetizados, nos tempos gerados por neon_style.py.
Uso: neon_audio.py sfx.json musica.wav saida.wav duracao"""
import sys, json, wave, numpy as np
ev = json.load(open(sys.argv[1])); mus = sys.argv[2]; out = sys.argv[3]; DUR = float(sys.argv[4]); SR = 44100
w = wave.open(mus); m = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).reshape(-1, 2).astype(np.float32) / 32768
n = int(DUR * SR); mix = np.zeros((n, 2), np.float32); mix[:min(n, len(m))] += m[:n] * 0.55
rng = np.random.default_rng(1)
def whoosh():
    L = int(0.42 * SR); t = np.arange(L) / SR; x = rng.standard_normal(L)
    # ruído filtrado com varredura (passa-banda simples por média móvel variável)
    y = np.zeros(L); a = 0.0
    for i in range(L):
        k = 0.02 + 0.25 * (i / L); a += k * (x[i] - a); y[i] = a
    env = np.sin(np.pi * t / t[-1]) ** 2; return y * env * 0.35
def tone(f0, f1, dur, harm=0.0, vol=0.25):
    L = int(dur * SR); t = np.arange(L) / SR; f = f0 + (f1 - f0) * (t / dur); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + harm * np.sin(2 * ph)) * np.exp(-t * 38) * vol
def tick():
    L = int(0.018 * SR); t = np.arange(L) / SR; return rng.standard_normal(L) * np.exp(-t * 400) * 0.05
LIB = {"whoosh": whoosh(), "pop": tone(950, 560, 0.12, 0.2, 0.22), "pop2": tone(1350, 980, 0.14, 0.35, 0.18)}
for t, kind in ev:
    s = LIB[kind] if kind != "tick" else tick(); i = int(t * SR)
    if i >= n: continue
    e = min(n, i + len(s)); mix[i:e, 0] += s[:e - i]; mix[i:e, 1] += s[:e - i]
mix /= max(1.0, np.abs(mix).max() / 0.9)
o = wave.open(out, "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((mix * 32767).astype(np.int16).tobytes()); o.close()
