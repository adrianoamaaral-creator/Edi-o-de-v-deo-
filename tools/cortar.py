"""Corta pausas da narração usando os tempos por palavra (palavras.json da transcrição).
Uso: python3 cortar.py <audio_original> <palavras.json> <saida.wav> <palavras_corte.json> [fim_s] [pausa_max_s]
Pausas > 0,25 s saem; bordas de 0,06 s antes e 0,10 s depois de cada bloco de fala.
"""
import json, subprocess, sys

def main():
    audio, pj, out, outj = sys.argv[1:5]
    fim = float(sys.argv[5]) if len(sys.argv) > 5 else 1e9
    maxp = float(sys.argv[6]) if len(sys.argv) > 6 else 0.16   # pausa máxima mantida entre blocos
    W = [w for w in json.load(open(pj)) if w["s"] < fim]
    bl = [[W[0]["s"], W[0]["e"]]]
    for w in W[1:]:
        if w["s"] - bl[-1][1] < 0.25: bl[-1][1] = w["e"]
        else: bl.append([w["s"], w["e"]])
    segs, t, mp = [], 0.0, []
    for s, e in bl:
        a = max(0, s - 0.06); z = e + 0.10
        if segs and a - segs[-1][1] > 0: a = max(segs[-1][1], s - max(0.06, maxp - 0.10))
        if segs and a < segs[-1][1]: a = segs[-1][1]
        segs.append((a, z)); mp.append((a, z, t)); t += z - a
    def conv(x):
        for a, z, t0 in mp:
            if a <= x <= z: return round(t0 + x - a, 3)
        for a, z, t0 in mp:
            if x < a: return round(t0, 3)
        return round(t, 3)
    json.dump([{"w": w["w"], "s": conv(w["s"]), "e": conv(w["e"])} for w in W], open(outj, "w"), ensure_ascii=False)
    f = [f"[0:a]atrim=start={a:.3f}:end={z:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.01,afade=t=out:st={z - a - 0.01:.3f}:d=0.01[a{i}];"
         for i, (a, z) in enumerate(segs)]
    f.append("".join(f"[a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[a]")
    open(out + ".filtro.txt", "w").write("\n".join(f))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", audio, "-filter_complex_script", out + ".filtro.txt", "-map", "[a]", "-ar", "48000", out], check=True)
    print("duração", round(t, 2))

if __name__ == "__main__":
    main()
