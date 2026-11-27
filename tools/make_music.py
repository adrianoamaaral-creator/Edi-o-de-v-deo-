"""Gera uma trilha original, suave e leve (pad + notas delicadas), para tocar baixinho sob a narração.
Uso: make_music.py duracao_s saida.wav"""
import sys, wave, numpy as np
DUR = float(sys.argv[1]); out = sys.argv[2]; SR = 44100
rng = np.random.default_rng(3)
n = int(DUR * SR); t = np.arange(n) / SR; L = np.zeros(n); R = np.zeros(n)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
# progressão calma (72 bpm, 2 compassos por acorde): Fmaj9 – Am7 – Dm9 – Bbmaj7 (F maior, tom quente)
chords = [[53, 60, 64, 67, 69], [57, 60, 64, 67, 71], [50, 57, 60, 64, 65], [46, 57, 62, 65, 69]]
bar = 60 / 72 * 4; clen = bar * 2
k = 0; c0 = 0.0
while c0 < DUR:
    notes = chords[k % 4]; s = int(c0 * SR); e = min(int((c0 + clen + 1.5) * SR), n); tt = np.arange(e - s) / SR
    env = np.minimum(tt / 1.2, 1) * np.exp(-np.maximum(tt - clen, 0) / 0.6)
    for j, m in enumerate(notes):
        f = hz(m); det = 1 + 0.0015 * (j - 2)
        tone = (np.sin(2 * np.pi * f * det * tt) + 0.25 * np.sin(2 * np.pi * 2 * f * tt) * 0.5) * env * (0.10 if j else 0.13)
        pan = 0.35 + 0.3 * (j / 4)
        L[s:e] += tone * (1 - pan); R[s:e] += tone * pan
    # notas delicadas (arpejo esparso, tipo celesta)
    beat = 60 / 72
    for b in range(8):
        if rng.random() < 0.55:
            m = notes[rng.integers(2, 5)] + 12; st = c0 + b * beat + rng.uniform(0, 0.08); s2 = int(st * SR)
            if s2 >= n: continue
            e2 = min(s2 + int(1.8 * SR), n); t2 = np.arange(e2 - s2) / SR; f = hz(m)
            p = (np.sin(2 * np.pi * f * t2) + 0.3 * np.sin(2 * np.pi * 3 * f * t2) * np.exp(-t2 * 6)) * np.exp(-t2 * 2.6) * 0.06
            pan = rng.uniform(0.3, 0.7); L[s2:e2] += p * (1 - pan); R[s2:e2] += p * pan
    k += 1; c0 += clen
# reverb simples (ruído com decaimento exponencial)
ir_t = np.arange(int(1.8 * SR)) / SR
def verb(x, seed):
    ir = np.random.default_rng(seed).standard_normal(len(ir_t)) * np.exp(-ir_t / 0.45); ir /= np.abs(ir).sum() / 6
    N = 1 << int(np.ceil(np.log2(len(x) + len(ir)))); return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
L = 0.7 * L + 0.3 * verb(L, 1); R = 0.7 * R + 0.3 * verb(R, 2)
fade = np.minimum(np.minimum(t / 2.0, 1), np.minimum((DUR - t) / 2.5, 1)).clip(0, 1); L *= fade; R *= fade
st = np.stack([L, R], 1); st /= np.abs(st).max() / 0.7
o = wave.open(out, "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((st * 32767).astype(np.int16).tobytes()); o.close()
print("ok", out, DUR)
