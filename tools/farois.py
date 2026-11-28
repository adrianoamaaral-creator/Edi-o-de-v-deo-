"""Regulador de altura dos faróis: o que significam 0, 1, 2 e 3. ~1min07, tela cheia.
Uso: python3 farois.py <saida.mp4> [inicio] [fim] [t1,t2,... => PNGs]
"""
import math, subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw, ImageFilter
from rotatoria import (W, H, FPS, F, SB, INTER, PAPER, CARD, INK, YEL, NAVY, RED, GREEN, WHITE,
                       paper_texture, tag, paste_scaled, pop, slide_in, stamp, stamp_img, clamp, prog, ease_out, ease_io)

ORANGE = (226, 168, 0); NIGHT = (28, 34, 58); SILVER = (206, 210, 216); BEAM = (255, 236, 150)
T = dict(n0=2.18, n1=3.14, n2=3.68, n3=4.18, quase=4.87, mas=6.09, regula=8.34, quando=10.59, peso=11.25,
         tras=12.53, frente=14.27, mirar=15.47, ofusca=17.68, ofw=18.18, cada=20.27, zero=22.86, ou=24.74, dia=27.14,
         um=28.40, dois=32.22, tres=36.70, maior=42.23, abaixa=44.33, como=46.98, parede=48.77, baixo=50.69,
         luz=52.26, abaixo=53.62, sem=55.18, aten=56.37, tabela=58.42, manual=60.05, salva=62.14, segue=65.02)
T_END = 67.0
BG = paper_texture(W, H, PAPER, 6).convert("RGBA")

# ------------------------------------------------------------ rodinha do regulador
def headlamp_icon(d, x, y, s=1.0, col=WHITE):
    d.arc([x - 10 * s, y - 34 * s, x + 54 * s, y + 34 * s], 270, 90, fill=col, width=int(6 * s))
    d.line([(x + 22 * s, y - 34 * s), (x + 22 * s, y + 34 * s)], fill=col, width=int(6 * s))
    for k in range(4):
        yy = y - 22 * s + k * 15 * s; d.line([(x - 40 * s, yy + 6 * s), (x + 6 * s, yy)], fill=col, width=int(5 * s))
    for sg in (-1, 1):
        d.line([(x - 60 * s, y), (x - 60 * s, y + sg * 44 * s)], fill=col, width=int(5 * s))
        d.polygon([(x - 70 * s, y + sg * 40 * s), (x - 50 * s, y + sg * 40 * s), (x - 60 * s, y + sg * 56 * s)], fill=col)

def dial(c, cx, cy, s, value, hi=None):
    """rodinha vertical; value (float) = número alinhado com a marca."""
    w, h = 300 * s, 620 * s
    L = Image.new("RGBA", (int(w) + 40, int(h) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rounded_rectangle([20, 20, 20 + w, 20 + h], 50 * s, fill=(26, 26, 28), outline=(70, 70, 74), width=int(6 * s))
    d.rounded_rectangle([20 + 30 * s, 20 + 40 * s, 20 + w - 30 * s, 20 + h - 40 * s], 30 * s, fill=(14, 14, 16))
    headlamp_icon(d, 20 + w / 2 + 6 * s, 20 + 120 * s, 0.9 * s)
    # janela da roda
    wx0, wy0, wx1, wy1 = 20 + 60 * s, 20 + 210 * s, 20 + w - 60 * s, 20 + h - 70 * s
    d.rounded_rectangle([wx0, wy0, wx1, wy1], 20 * s, fill=(40, 40, 44))
    midy = (wy0 + wy1) / 2; step = 92 * s
    for k in range(-1, 5):
        y = midy - (k - value) * step
        if wy0 + 34 * s < y < wy1 - 34 * s:
            on = hi is not None and k == hi
            if on: d.rounded_rectangle([wx0 + 70 * s, y - 40 * s, wx1 - 8 * s, y + 40 * s], 10 * s, fill=YEL)
            if 0 <= k <= 3:
                f = F(INTER, int(64 * s)); txt = str(k); tw = d.textlength(txt, font=f)
                d.text((wx0 + 70 * s + (wx1 - wx0 - 78 * s - tw) / 2, y - 38 * s), txt, font=f, fill=INK if on else WHITE)
            d.line([(wx0 + 70 * s, y + step / 2), (wx1 - 8 * s, y + step / 2)], fill=(20, 20, 22), width=int(4 * s))
    for k in range(int((wy1 - wy0) / (14 * s))):                 # serrilhado da roda
        yy = wy0 + 8 * s + k * 14 * s + ((value * step) % (14 * s))
        if yy < wy1 - 6 * s: d.line([(wx0 + 10 * s, yy), (wx0 + 56 * s, yy)], fill=(90, 90, 96), width=int(5 * s))
    d.rounded_rectangle([wx1 + 10 * s, midy - 8 * s, wx1 + 40 * s, midy + 8 * s], 4 * s, fill=WHITE)   # marca
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 90), (0, 0), L.split()[3])
    c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (int(cx - L.width / 2) + 8, int(cy - L.height / 2) + 14))
    c.alpha_composite(L, (int(cx - L.width / 2), int(cy - L.height / 2)))

# ------------------------------------------------------------ carro de lado
def car_body(load):
    """carro visto de lado (frente para a direita). load: 0 só motorista, 1 cheio, 2 cheio+malas, 3 motorista+malas pesadas"""
    s = Image.new("RGBA", (560, 230), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.polygon([(20, 150), (30, 95), (120, 85), (190, 30), (360, 26), (440, 88), (530, 105), (545, 150), (530, 180), (30, 180)],
              fill=SILVER, outline=(60, 62, 70))
    d.polygon([(200, 42), (300, 40), (300, 92), (150, 92)], fill=(70, 86, 110))
    d.polygon([(312, 40), (352, 40), (420, 92), (312, 92)], fill=(70, 86, 110))
    d.polygon([(50, 98), (118, 92), (140, 92), (140, 100), (54, 108)], fill=(70, 86, 110))
    d.ellipse([515, 112, 545, 132], fill=(255, 240, 180))         # farol
    d.rectangle([18, 112, 30, 130], fill=(220, 40, 40))           # lanterna
    heads = {0: [355], 1: [355, 260, 200], 2: [355, 260, 200], 3: [355]}[load]
    for hx in heads: d.ellipse([hx - 16, 52, hx + 16, 84], fill=(40, 34, 30))
    if load in (2, 3):                                            # malas no porta-malas
        for k, (bx, by) in enumerate([(56, 100), (88, 96)] + ([(60, 70)] if load == 3 else [])):
            d.rounded_rectangle([bx, by - 30, bx + 30, by], 5, fill=(140, 90, 50), outline=(80, 50, 30), width=3)
    return s

def beam(c, x, y, ang, length=700, spread=6, alpha=1.0):
    ov = Image.new("RGBA", c.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for k, (sp, al) in enumerate([(spread * 1.4, 50), (spread, 80), (spread * 0.5, 110)]):
        a1, a2 = math.radians(ang + sp), math.radians(ang - sp)
        d.polygon([(x, y), (x + length * math.cos(a1), y - length * math.sin(a1)), (x + length * math.cos(a2), y - length * math.sin(a2))],
                  fill=BEAM + (int(al * alpha),))
    c.alpha_composite(ov.filter(ImageFilter.GaussianBlur(6)))

def draw_car(c, x, y, pitch, load, beam_ang, trailer=False, beam_len=700, beam_alpha=1.0):
    """x,y = ponto de contato da roda dianteira. pitch>0 = frente levanta."""
    body = car_body(load)
    pivot = (480, 180)                                            # roda dianteira no sprite
    R = Image.new("RGBA", (1200, 700), (0, 0, 0, 0)); R.alpha_composite(body, (600 - pivot[0], 350 - pivot[1]))
    R = R.rotate(pitch, center=(600, 350), resample=Image.BICUBIC)
    sc = 1.0
    if trailer:
        d = ImageDraw.Draw(c); tx = x - 780
        d.rectangle([tx, y - 150, tx + 150, y - 40], fill=(110, 112, 118), outline=INK, width=4)
        d.line([(tx + 150, y - 50), (tx + 330, y - 50)], fill=INK, width=8)
        d.ellipse([tx + 40, y - 70, tx + 110, y], fill=(30, 30, 32))
    c.alpha_composite(R, (int(x - 600), int(y - 350 - 26)))
    d = ImageDraw.Draw(c)
    for wx in (x - 380, x):                                       # rodas
        d.ellipse([wx - 42, y - 84 + (0 if wx == x else 0), wx + 42, y], fill=(24, 24, 26)); d.ellipse([wx - 20, y - 62, wx + 20, y - 22], fill=(150, 150, 156))
    a = math.radians(pitch); hx, hy = 530 - pivot[0], 122 - pivot[1]
    bx = x + hx * math.cos(a) + hy * math.sin(a); by = y - 26 + (-hx * math.sin(a) + hy * math.cos(a))
    if beam_ang is not None: beam(c, bx, by, beam_ang, beam_len, alpha=beam_alpha)
    return bx, by

def night_panel(c, y0, y1, ground=None):
    d = ImageDraw.Draw(c); d.rounded_rectangle([30, y0, 1050, y1], 36, fill=NIGHT)
    g = ground if ground is not None else y1 - 90
    d.rectangle([30, g, 1050, y1 - 30], fill=(58, 58, 68)); d.rounded_rectangle([30, y1 - 60, 1050, y1], 30, fill=(58, 58, 68))
    for x in range(60, 1040, 110): d.rectangle([x, g + 26, x + 60, g + 32], fill=(230, 230, 230))
    for (sx, sy) in [(120, y0 + 60), (330, y0 + 110), (620, y0 + 50), (880, y0 + 90), (980, y0 + 40)]:
        d.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(240, 240, 255))
    return g

def oncoming(c, x, y, glare):
    s = car_body(0).transpose(Image.FLIP_LEFT_RIGHT).resize((392, 161))
    c.alpha_composite(s, (int(x), int(y - 161 + 10)))
    d = ImageDraw.Draw(c)
    for wx in (x + 60, x + 330): d.ellipse([wx - 30, y - 58, wx + 30, y + 2], fill=(24, 24, 26))
    if glare > 0:
        ov = Image.new("RGBA", c.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov); gx, gy = x + 150, y - 110
        for k in range(12):
            a = math.radians(k * 30); r = 120 * glare
            od.line([(gx, gy), (gx + r * math.cos(a), gy + r * math.sin(a))], fill=(255, 250, 200, 220), width=10)
        od.ellipse([gx - 50 * glare, gy - 50 * glare, gx + 50 * glare, gy + 50 * glare], fill=(255, 255, 230, 230))
        c.alpha_composite(ov.filter(ImageFilter.GaussianBlur(4)))

STAMPS = {"OFUS": stamp_img("OFUSCOU!", RED, size=110), "OK": stamp_img("CERTO", GREEN, size=90, rot=6)}

def top_card(c):
    d = ImageDraw.Draw(c)
    d.rectangle([40, 200, 1040, 336], fill=CARD); d.rectangle([40, 332, 1040, 336], fill=(210, 196, 166))
    f = F(SB, 44); t = "REGULADOR DE ALTURA DOS FARÓIS"; d.text(((W - d.textlength(t, font=f)) / 2, 222), t, font=f, fill=INK)
    f2 = F(SB, 26); h = "@INSTRUTORGUSTAVOVIEIRA"; d.text(((W - d.textlength(h, font=f2)) / 2, 288), h, font=f2, fill=(120, 108, 90))

def lower(c, t, text, t0, t1, bg, fg=WHITE, rot=-2, y=1600, size=60, **kw):
    if t0 <= t < t1 + 0.2:
        a, dy = slide_in(t, t0, t1); paste_scaled(c, tag(text, size, bg, fg, rot, **kw), (540, y + dy), 1, a)

LOAD_LBL = ["só motorista (ou + passageiro na frente)", "todos os bancos ocupados", "bancos cheios + porta-malas carregado", "porta-malas pesado ou REBOQUE"]
NUM_T = ["zero", "um", "dois", "tres"]

def frame(t):
    c = BG.copy(); d = ImageDraw.Draw(c)
    if t < T["regula"]:                                           # rodinha grande
        hi = None; val = 0
        for k, key in enumerate(["n0", "n1", "n2", "n3"]):
            if t >= T[key]: hi = k
        if hi is not None: val = drive(t, T[["n0", "n1", "n2", "n3"][hi]], T[["n0", "n1", "n2", "n3"][hi]] + 0.3, max(0, hi - 1), hi)
        dial(c, 540, 920, 1.25, val, hi)
        paste_scaled(c, tag("sabe essa rodinha do painel?", 62, WHITE, INK, 2), (540, 470), pop(t, 0.05, 0.3))
        lower(c, t, "quase ninguém usa…", T["quase"], T["mas"], ORANGE, INK, size=62, y=1480)
        lower(c, t, "mas é MUITO importante à noite", T["mas"], T["regula"], NAVY, size=60, y=1480)
    elif t < T["cada"]:                                           # por que importa
        g = night_panel(c, 420, 1400)
        pitch = 0.0
        if t >= T["tras"]: pitch = 5 * ease_out(prog(t, T["tras"], T["frente"] + 0.4))
        beam_ang = pitch * 1.8 if t >= T["regula"] else None
        load_drop = prog(t, T["peso"], T["peso"] + 0.5)
        load = 2 if t >= T["peso"] + 0.5 else 0
        if T["regula"] <= t < T["quando"]:                        # demonstração: o facho sobe e desce
            beam_ang = 6 * math.sin((t - T["regula"]) * 3)
        draw_car(c, 520, g + 20, pitch, load, beam_ang, beam_len=650)
        if T["peso"] <= t < T["peso"] + 0.5:                      # malas caindo no porta-malas
            for k in range(2):
                yy = 520 + 360 * ease_io(load_drop); d.rounded_rectangle([170 + k * 40, yy - 40, 210 + k * 40, yy], 6, fill=(140, 90, 50), outline=(80, 50, 30), width=3)
        if t >= T["ofusca"] - 0.6:
            oncoming(c, 680, g + 10, ease_out(prog(t, T["ofusca"], T["ofusca"] + 0.4)))
        if T["ofw"] <= t < T["cada"]:
            sc, sh = stamp(t, T["ofw"]); paste_scaled(c, STAMPS["OFUS"], (540 + sh, 600), sc, 1 - prog(t, T["cada"] - 0.2, T["cada"]))
        if t >= T["regula"] and t < T["quando"]:
            dial(c, 170, 760, 0.45, 1.5 + 1.5 * math.sin((t - T["regula"]) * 3), None)
        lower(c, t, "ela regula a ALTURA dos faróis", T["regula"], T["quando"], NAVY)
        lower(c, t, "peso atrás → traseira abaixa", T["quando"], T["frente"], ORANGE, INK)
        lower(c, t, "a frente levanta", T["frente"], T["mirar"], ORANGE, INK, rot=2)
        lower(c, t, "o farol mira PARA CIMA", T["mirar"], T["ofusca"], RED)
        lower(c, t, "e ofusca quem vem na frente", T["ofusca"], T["cada"], RED, rot=2)
    elif t < T["como"]:                                           # cada número
        idx = 0
        for k, key in enumerate(NUM_T):
            if t >= T[key]: idx = k
        tk = T[NUM_T[idx]]
        val = drive(t, tk, tk + 0.35, max(0, idx - 1), idx) if idx > 0 else 0
        hi = idx if t >= T["zero"] else None
        dial(c, 200, 690, 0.55, val, hi)
        if t >= T["zero"]:
            num = tag(str(idx), 230, YEL, INK, -3, pad=(50, 10)); paste_scaled(c, num, (600, 670), pop(t, tk, 0.3))
            paste_scaled(c, tag(LOAD_LBL[idx], 50 if idx != 0 else 44, NAVY, WHITE, 2), (540, 960), pop(t, tk + 0.25, 0.3))
        g = night_panel(c, 1040, 1560)
        pitch = [0.5, 1.5, 3.0, 3.5][idx] if t >= T["zero"] else 0.5
        comp = [0.5, 1.5, 3.0, 3.5][idx] if t >= T["zero"] else 0.5
        p = ease_out(prog(t, tk, tk + 0.5))
        bang = (pitch * 1.8 - comp * 1.8 * p) - 1.0 if t < T["maior"] else -1.0 - 3.5 * ease_io(prog(t, T["abaixa"], T["abaixa"] + 0.6)) * math.sin((t - T["abaixa"]) * 2.5) ** 2
        draw_car(c, 800 if idx == 3 else 600, g + 20, pitch, idx if t >= T["zero"] else 0, bang, trailer=(idx == 3), beam_len=520)
        lower(c, t, "cada número = uma carga", T["cada"], T["zero"], NAVY, y=500)
        lower(c, t, "a posição do dia a dia", T["dia"], T["um"], GREEN, y=1660, size=56)
        lower(c, t, "número MAIOR = farol mais BAIXO", T["maior"], T["como"], RED, y=1660, size=56)
    elif t < T["aten"]:                                           # teste da parede
        g = night_panel(c, 420, 1400)
        d.rectangle([880, 470, 1030, g + 30], fill=(170, 160, 146)); d.rectangle([880, 470, 892, g + 30], fill=(130, 122, 110))
        on = t >= T["baixo"]
        bx, by = draw_car(c, 470, g + 20, 0, 0, -2.2 if on else None, beam_len=420, beam_alpha=1.0 if on else 0)
        if t >= T["luz"]:                                         # linha da altura do farol
            dd = ImageDraw.Draw(c)
            for x in range(int(bx), 1030, 26): dd.line([(x, by), (x + 14, by)], fill=WHITE, width=4)
            lab = tag("altura do farol", 34, WHITE, INK, 0, font=INTER); paste_scaled(c, lab, (760, by - 50), pop(t, T["luz"], 0.3))
        if on:
            spot_y = by + 60; ov = Image.new("RGBA", c.size, (0, 0, 0, 0))
            ImageDraw.Draw(ov).ellipse([890, spot_y - 70, 1030, spot_y + 70], fill=BEAM + (200,)); c.alpha_composite(ov.filter(ImageFilter.GaussianBlur(10)))
        if t >= T["abaixo"]:
            sc, sh = stamp(t, T["sem"]) if t >= T["sem"] else (0, 0)
            if sc: paste_scaled(c, STAMPS["OK"], (300 + sh, 600), sc)
        lower(c, t, "como saber se está certo?", T["como"], T["parede"], NAVY)
        lower(c, t, "de frente para uma PAREDE", T["parede"], T["baixo"], NAVY, rot=2)
        lower(c, t, "com o farol BAIXO aceso", T["baixo"], T["luz"], ORANGE, INK)
        lower(c, t, "a luz um pouco ABAIXO do farol", T["abaixo"], T["sem"], GREEN, size=56)
        lower(c, t, "sem subir!", T["sem"], T["aten"], GREEN, rot=2, size=72)
    else:                                                         # manual
        s = pop(t, T["aten"], 0.35)
        book = Image.new("RGBA", (420, 520), (0, 0, 0, 0)); bd = ImageDraw.Draw(book)
        bd.rounded_rectangle([20, 20, 400, 500], 20, fill=NAVY, outline=INK, width=8); bd.rectangle([20, 20, 70, 500], fill=(36, 40, 62))
        bd.text((100, 120), "MANUAL", font=F(SB, 64), fill=WHITE); bd.text((100, 200), "DO", font=F(SB, 48), fill=WHITE); bd.text((100, 260), "VEÍCULO", font=F(SB, 58), fill=WHITE)
        headlamp_icon(bd, 230, 420, 0.8)
        paste_scaled(c, book, (540, 860), s)
        lower(c, t, "atenção: cada carro tem a sua tabela", T["aten"], T["manual"], RED, size=54, y=1300)
        lower(c, t, "confere no MANUAL do seu veículo", T["manual"], T["salva"], NAVY, size=56, y=1300)
    top_card(c)
    if t >= T["salva"]:
        a = ease_out(prog(t, T["salva"], T["salva"] + 0.3)); c.alpha_composite(Image.new("RGBA", (W, H), PAPER + (int(235 * a),)))
        if t < T["segue"]:
            s = pop(t, T["salva"], 0.35); bounce = abs(math.sin((t - T["salva"]) * 5)) * 30 if t > T["salva"] + 0.4 else 0
            icon = Image.new("RGBA", (260, 320), (0, 0, 0, 0)); ImageDraw.Draw(icon).polygon([(30, 20), (230, 20), (230, 300), (130, 220), (30, 300)], fill=YEL, outline=INK, width=10)
            paste_scaled(c, icon, (540, 760 - bounce), s)
            paste_scaled(c, tag("SALVA esse vídeo", 90, NAVY, WHITE, -2), (540, 1060), pop(t, T["salva"] + 0.2, 0.3))
            paste_scaled(c, tag("pra lembrar na próxima viagem", 60, WHITE, INK, 2), (540, 1200), pop(t, T["salva"] + 1.0, 0.3))
        else:
            paste_scaled(c, tag("Me segue para mais", 74, NAVY, WHITE, -2), (540, 880), pop(t, T["segue"], 0.3))
            paste_scaled(c, tag("dicas de trânsito", 92, YEL, INK, 2), (540, 1020), pop(t, T["segue"] + 0.35, 0.3))
            q = ease_out(prog(t, T["segue"] + 0.7, T["segue"] + 1.0))
            if q > 0: paste_scaled(c, tag("@instrutorgustavovieira", 52, WHITE, INK, 0, font=INTER), (540, 1200 + (1 - q) * 30), 1, q)
    return c.convert("RGB")

def drive(t, t0, t1, a, b):
    return a + (b - a) * ease_io(prog(t, t0, t1))

def main():
    out = sys.argv[1]; t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0; t1 = float(sys.argv[3]) if len(sys.argv) > 3 else T_END
    if len(sys.argv) > 4:
        for tt in sys.argv[4].split(","): frame(float(tt)).save(f"{out}_{float(tt):05.2f}.png")
        return
    n = int(round((t1 - t0) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                          "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(frame(t0 + i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
