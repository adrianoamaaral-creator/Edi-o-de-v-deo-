"""Alinha o texto lido (TTS) com os blocos de fala detectados por silêncio, sem transcrição.
Uso: python3 alinhar.py <audio> <texto.txt> <saida_blocos.json> [ruido_dB] [silencio_min_s]
Agrupa palavras consecutivas em cada bloco de fala, minimizando a diferença entre a duração
do bloco e a duração prevista pelas sílabas, e preferindo quebras em pontuação.
"""
import json, re, subprocess, sys

def silences(audio, noise=-35, dmin=0.2):
    r = subprocess.run(["ffmpeg", "-i", audio, "-af", f"silencedetect=noise={noise}dB:d={dmin}", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    v = [float(x) for x in re.findall(r"silence_(?:start|end): ([0-9.]+)", r)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", audio],
                               capture_output=True, text=True).stdout)
    st = [0.0] + v[1::2]; en = v[0::2] + [dur]
    if len(st) > len(en): st = st[:len(en)]
    return [(s, e) for s, e in zip(st, en) if e - s > 0.08], dur

def syl(w):
    w = w.lower()
    n = len(re.findall(r"[aeiouáéíóúâêôãõày]+", w))
    if re.fullmatch(r"[a-z]", w): n = 1
    return max(1, n)

def main():
    audio, txt, out = sys.argv[1:4]
    noise = float(sys.argv[4]) if len(sys.argv) > 4 else -35
    dmin = float(sys.argv[5]) if len(sys.argv) > 5 else 0.2
    blocks, dur = silences(audio, noise, dmin)
    words = open(txt, encoding="utf-8").read().split()
    sy = [syl(w) for w in words]
    punct = [bool(re.search(r"[,.?:!;]$", w)) for w in words]
    rate = sum(sy) / sum(e - s for s, e in blocks)
    n, m = len(words), len(blocks); INF = float("inf")
    cs = [0]
    for v in sy: cs.append(cs[-1] + v)
    dp = [[INF] * (m + 1) for _ in range(n + 1)]; bk = [[None] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0
    for j in range(1, m + 1):
        s, e = blocks[j - 1]; d = e - s
        for i in range(1, n + 1):
            for k in range(max(0, i - 30), i):
                if dp[k][j - 1] == INF: continue
                pred = (cs[i] - cs[k]) / rate
                c = dp[k][j - 1] + (d - pred) ** 2 / (0.25 + 0.1 * pred) + (0 if punct[i - 1] or i == n else 1.5)
                if c < dp[i][j]: dp[i][j] = c; bk[i][j] = k
    res, i, j = [], n, m
    while j > 0:
        k = bk[i][j]; res.append([blocks[j - 1][0], blocks[j - 1][1], " ".join(words[k:i])]); i, j = k, j - 1
    res.reverse()
    json.dump({"dur": dur, "blocos": res}, open(out, "w"), ensure_ascii=False, indent=0)
    for k, (s, e, t) in enumerate(res):
        print(f"{k:2d} {s:6.2f} {e:6.2f} {e - s:5.2f} {(sum(syl(w) for w in t.split()) / rate):5.2f}  {t}")

if __name__ == "__main__":
    main()
