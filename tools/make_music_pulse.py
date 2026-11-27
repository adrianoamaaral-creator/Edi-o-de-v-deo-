"""Trilha original elegante com pulso (96 bpm): pad quente, baixo, kick suave, shaker e pluck.
Os cortes do vídeo semijoias_valores.py caem nas batidas. Uso: make_music_pulse.py duracao_s saida.wav"""
import sys, wave, numpy as np
DUR = float(sys.argv[1]); out = sys.argv[2]; SR = 44100; BPM = 96; B = 60 / BPM
rng = np.random.default_rng(11)
n = int(DUR * SR); t = np.arange(n) / SR; L = np.zeros(n); R = np.zeros(n)
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def add(x, s0, pan=0.5, g=1.0):
    s = int(s0 * SR)
    if s >= n: return
    e = min(n, s + len(x)); L[s:e] += x[:e - s] * (1 - pan) * g; R[s:e] += x[:e - s] * pan * g
# Am9 – Fmaj7 – Cmaj7/E – G6, 2 compassos cada
chords = [[45, 60, 64, 67, 71], [41, 57, 60, 64, 69], [40, 55, 59, 64, 67], [43, 55, 59, 62, 64]]
bar = 4 * B; clen = 2 * bar; nb = int(DUR / B) + 1
import os
INTRO_BEATS = int(os.environ.get("INTRO_BEATS", 6))   # pulso entra depois da abertura
for c in range(int(DUR / clen) + 1):
    notes = chords[c % 4]; c0 = c * clen; tt = np.arange(int((clen + 1.2) * SR)) / SR
    env = np.minimum(tt / 0.9, 1) * np.exp(-np.maximum(tt - clen, 0) / 0.4)
    for j, m in enumerate(notes[1:]):
        f = hz(m); tone = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * f * 1.003 * tt) + 0.12 * np.sin(2 * np.pi * 2 * f * tt)) * env * 0.055
        add(tone, c0, 0.3 + 0.1 * j)
    # baixo: nota fundamental em semínimas pontuadas
    for k in range(8):
        bt = c0 + k * B
        if bt / B < INTRO_BEATS - 0.01: continue
        tb = np.arange(int(B * 0.95 * SR)) / SR; f = hz(notes[0])
        add(np.sin(2 * np.pi * f * tb) * np.exp(-tb * 3.2) * np.minimum(tb / 0.01, 1) * 0.30, bt, 0.5)
    # pluck (arpejo discreto em colcheias)
    for k in range(16):
        if rng.random() < 0.45:
            st = c0 + k * B / 2; m = notes[1 + rng.integers(0, 4)] + 12; tp = np.arange(int(0.9 * SR)) / SR; f = hz(m)
            p = (np.sin(2 * np.pi * f * tp) + 0.4 * np.sin(2 * np.pi * 2 * f * tp) * np.exp(-tp * 8)) * np.exp(-tp * 5) * 0.045
            add(p, st, rng.uniform(0.25, 0.75))
for b in range(nb):
    bt = b * B
    if b < INTRO_BEATS: continue
    tk = np.arange(int(0.35 * SR)) / SR      # kick suave
    f = 50 + 70 * np.exp(-tk * 30); ph = 2 * np.pi * np.cumsum(f) / SR
    add(np.sin(ph) * np.exp(-tk * 9) * 0.42, bt, 0.5)
    th = np.arange(int(0.08 * SR)) / SR      # shaker no contratempo
    hs = rng.standard_normal(len(th)); hs = np.diff(np.concatenate([[0], hs])) * np.exp(-th * 45) * 0.05
    add(hs, bt + B / 2, 0.62); add(hs * 0.5, bt + B / 4 * 3, 0.4)
    if b % 4 == 2:                           # estalo leve (clap) no 3º tempo
        tc = np.arange(int(0.15 * SR)) / SR; cl = rng.standard_normal(len(tc)) * np.exp(-tc * 28) * 0.06
        add(np.diff(np.concatenate([[0], cl])), bt, 0.5)
# riser antes da entrada do pulso
rs = INTRO_BEATS * B - 1.2; tr = np.arange(int(1.2 * SR)) / SR
nz = rng.standard_normal(len(tr)); nz = np.diff(np.concatenate([[0], nz])); add(nz * (tr / 1.2) ** 2 * 0.07, rs, 0.5)
ir_t = np.arange(int(1.6 * SR)) / SR
def verb(x, seed):
    ir = np.random.default_rng(seed).standard_normal(len(ir_t)) * np.exp(-ir_t / 0.35); ir /= np.abs(ir).sum() / 5
    N = 1 << int(np.ceil(np.log2(len(x) + len(ir)))); return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)[:len(x)]
L = 0.78 * L + 0.22 * verb(L, 1); R = 0.78 * R + 0.22 * verb(R, 2)
fade = np.minimum(np.minimum(t / 0.8, 1), np.minimum((DUR - t) / 1.6, 1)).clip(0, 1); L *= fade; R *= fade
st = np.stack([L, R], 1); st /= np.abs(st).max() / 0.8
o = wave.open(out, "wb"); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes((st * 32767).astype(np.int16).tobytes()); o.close()
print("ok", out, DUR)
