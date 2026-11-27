"""Gera uma trilha suave e original (piano elétrico + pad + baixo), sem direitos de terceiros.
Uso: python3 tools/musica_suave.py SAIDA.wav DURACAO_SEGUNDOS
"""
import sys, wave
import numpy as np

SR = 44100
BPM = 76
BEAT = 60 / BPM
out, dur = sys.argv[1], float(sys.argv[2])
n = int(SR * (dur + 2))
L = np.zeros(n); R = np.zeros(n)

def hz(m): return 440 * 2 ** ((m - 69) / 12)

# Fmaj7 – Am7 – Dm9 – Bbmaj7(#11) ... (notas MIDI)
CHORDS = [
    (41, [65, 69, 72, 76]),
    (45, [64, 67, 69, 72]),
    (38, [65, 69, 72, 76]),
    (46, [62, 65, 69, 74]),
]
BAR = 4 * BEAT
t_all = np.arange(n) / SR

def add(sig, start, pan=0.0):
    i = int(start * SR)
    if i >= n: return
    sig = sig[: n - i]
    L[i:i + len(sig)] += sig * (1 - pan) * 0.5 * 2
    R[i:i + len(sig)] += sig * (1 + pan) * 0.5 * 2

def epiano(f, d, vel):
    t = np.arange(int(SR * d)) / SR
    env = np.exp(-3.2 * t) * (1 - np.exp(-t * 400))
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-6 * t) + 0.12 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-9 * t)
    return vel * env * s

def pad(notes, d):
    t = np.arange(int(SR * d)) / SR
    env = np.minimum(1, t / 1.2) * np.minimum(1, (d - t) / 1.0).clip(0)
    s = np.zeros_like(t)
    for m in notes:
        f = hz(m - 12)
        for det in (-0.12, 0.12):
            s += np.sin(2 * np.pi * (f + det) * t + 0.3 * np.sin(2 * np.pi * 0.2 * t))
    return 0.05 * env * s / len(notes)

def bass(f, d):
    t = np.arange(int(SR * d)) / SR
    env = np.minimum(1, t / 0.02) * np.exp(-0.8 * t)
    return 0.22 * env * (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t))

rng = np.random.default_rng(7)
bar = 0
t0 = 0.0
pattern = [0, 2, 1, 3, 2, 1, 3, 2]  # arpejo em colcheias
while t0 < dur + 1:
    root, notes = CHORDS[bar % 4]
    add(pad(notes, BAR + 1.0), t0, 0.0)
    add(bass(hz(root), BAR), t0, 0.0)
    for k, idx in enumerate(pattern):
        if bar % 2 == 1 and k == 7:  # respiro
            continue
        vel = 0.10 + 0.03 * rng.random() + (0.03 if k % 4 == 0 else 0)
        f = hz(notes[idx])
        add(epiano(f, 1.6, vel), t0 + k * BEAT / 2 + 0.005 * rng.random(), pan=(-0.3 if idx % 2 else 0.3))
    bar += 1
    t0 += BAR

st = np.stack([L, R], 1)[: int(SR * dur)]
# fade in/out
fi, fo = int(SR * 1.5), int(SR * 2.5)
st[:fi] *= np.linspace(0, 1, fi)[:, None]
st[-fo:] *= np.linspace(1, 0, fo)[:, None]
st = st / np.abs(st).max() * 0.7
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
