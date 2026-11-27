"""Mixa voz + efeitos sonoros e junta com o vídeo desenhado.
Uso: python3 mix_rotatoria.py <video.mp4> <voz.wav> <pasta_sfx> <saida.mp4> [inicio] [fim]
"""
import json, subprocess, sys

SFX = [  # (tempo, arquivo, ganho dB)
    (0.02, "whoosh", -17), (1.00, "pop", -18), (4.22, "pop", -18), (7.05, "whoosh", -19),
    (8.53, "impacto", -11), (9.20, "whoosh", -19), (10.35, "pop", -18), (13.43, "pop", -18),
    (15.90, "tique", -16), (17.47, "whoosh", -19), (19.95, "pop", -18), (22.75, "pop", -18),
    (26.46, "whoosh", -18), (29.02, "whoosh", -18), (32.35, "impacto", -12), (34.93, "pop", -17),
    (37.78, "pop", -18), (38.98, "pop", -18), (40.35, "pop", -18), (41.83, "ding", -16),
]

def run(cmd): return subprocess.run(cmd, check=True, capture_output=True, text=True)

def main():
    video, voz, sfxdir, out = sys.argv[1:5]
    t0 = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
    t1 = float(sys.argv[6]) if len(sys.argv) > 6 else 1e9
    sel = [(t - t0, f, g) for (t, f, g) in SFX if t0 <= t < t1]
    inputs = ["-ss", f"{t0}", "-t", f"{t1 - t0}", "-i", voz]
    chains, labels = [], ["[0:a]"]
    for i, (t, f, g) in enumerate(sel, start=1):
        inputs += ["-i", f"{sfxdir}/{f}.wav"]
        ms = int(t * 1000)
        chains.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=mono,volume={g}dB,adelay={ms}|{ms}[s{i}]")
        labels.append(f"[s{i}]")
    fc = ";".join(chains + [f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first[m]"])
    mix = out + ".mix.wav"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[m]", "-ar", "48000", mix])
    # loudnorm em duas passadas, alvo -14 LUFS
    r = subprocess.run(["ffmpeg", "-i", mix, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", mix, "-af", ln, "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out])

if __name__ == "__main__":
    main()
