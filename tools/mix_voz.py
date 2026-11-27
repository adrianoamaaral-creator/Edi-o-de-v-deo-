"""Mixa narração + efeitos + música leve e junta ao vídeo.

Uso: python3 tools/mix_voz.py VIDEO.mp4 VOZ.wav MUSICA.wav SAIDA.mp4
Os efeitos vêm de anim_ajustes_voz.SONS. Música ~17 dB abaixo da voz, abaixando quando há fala.
Volume final: loudnorm em duas passadas, alvo -14 LUFS.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from anim_ajustes_voz import DUR, SONS  # noqa: E402

video, voz, musica, out = sys.argv[1:5]
tmp = tempfile.mkdtemp()


def ff(*args):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


RECEITAS = {
    "whoosh": ["-f", "lavfi", "-i", "anoisesrc=d=0.45:c=pink:a=0.5", "-af",
               "highpass=f=400,lowpass=f=5000,afade=t=in:d=0.25,afade=t=out:st=0.25:d=0.2"],
    "pop": ["-f", "lavfi", "-i", "aevalsrc='0.8*sin(2*PI*(500+3000*exp(-30*t))*t)*exp(-25*t)':d=0.15:s=48000"],
    "ding": ["-f", "lavfi", "-i", "aevalsrc='0.5*(sin(2*PI*1318*t)+0.5*sin(2*PI*2637*t))*exp(-5*t)':d=0.9:s=48000"],
    "impacto": ["-f", "lavfi", "-i", "aevalsrc='0.9*sin(2*PI*55*t)*exp(-7*t)+0.2*(random(0)*2-1)*exp(-30*t)':d=0.5:s=48000"],
    "tique": ["-f", "lavfi", "-i", "aevalsrc='0.6*sin(2*PI*2200*t)*exp(-120*t)':d=0.04:s=48000"],
}
for nome, args in RECEITAS.items():
    ff(*args, "-ar", "48000", os.path.join(tmp, nome + ".wav"))

# nunca dois sons a menos de 0,6 s
sons, ult = [], -9
for s, t, v in sorted(SONS, key=lambda x: x[1]):
    if t - ult >= 0.6 and t < DUR:
        sons.append((s, t, v))
        ult = t

ins, fc = [], []
for i, (s, t, v) in enumerate(sons):
    ins += ["-i", os.path.join(tmp, s + ".wav")]
    ms = int(t * 1000)
    fc.append(f"[{i}:a]aformat=channel_layouts=stereo,volume={v}dB,adelay={ms}|{ms},apad,atrim=0:{DUR}[s{i}];")
fc.append("".join(f"[s{i}]" for i in range(len(sons))) + f"amix=inputs={len(sons)}:normalize=0,atrim=0:{DUR}[a]")
sfx = os.path.join(tmp, "sfx.wav")
ff(*ins, "-filter_complex", "".join(fc), "-map", "[a]", "-ar", "48000", sfx)

nv = len(sons)
mix = os.path.join(tmp, "mix.wav")
graph = (
    f"[0:a]highpass=f=80,volume=15dB,alimiter=limit=0.9,aformat=channel_layouts=stereo,apad,atrim=0:{DUR},asplit[v1][v2];"
    f"[1:a]volume=-10dB,apad,atrim=0:{DUR}[m];"
    f"[m][v2]sidechaincompress=threshold=0.03:ratio=3:attack=20:release=400[md];"
    f"[2:a]apad,atrim=0:{DUR}[fx];"
    f"[v1][md][fx]amix=inputs=3:normalize=0,atrim=0:{DUR}[a]"
)
ff("-i", voz, "-i", musica, "-i", sfx, "-filter_complex", graph, "-map", "[a]", "-ar", "48000", mix)

r = subprocess.run(["ffmpeg", "-i", mix, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                   capture_output=True, text=True).stderr
m = json.loads(re.findall(r"\{[^{}]*\}", r, re.S)[-1])
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
      f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
final = os.path.join(tmp, "final.wav")
ff("-i", mix, "-af", ln, "-ar", "48000", final)
ff("-i", video, "-i", final, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
   "-shortest", "-movflags", "+faststart", out)
print("sons:", len(sons), "de", len(SONS))
