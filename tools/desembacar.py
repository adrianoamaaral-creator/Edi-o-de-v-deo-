"""Como desembaçar o para-brisa (passo a passo, visão de dentro do carro). ~1min02, tela cheia.
Uso: python3 desembacar.py <saida.mp4> [inicio] [fim] [t1,t2,... => PNGs]
"""
import math, subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from rotatoria import (W, H, FPS, F, SB, INTER, PAPER, CARD, INK, YEL, NAVY, RED, GREEN, WHITE,
                       paper_texture, tag, paste_scaled, pop, slide_in, stamp, stamp_img, clamp, prog, ease_out, ease_io, drive)

rng = np.random.default_rng(11)
ORANGE = (226, 168, 0); BLUE = (52, 110, 210); AMBER = (255, 176, 40)
T = dict(faz=3.11, prim=6.08, umid=8.81, frio=10.9, got=12.53, entao=13.46, tirar=14.44,
         p1=16.37, liga=17.42, ele=19.05, mesmo=21.11, p2=23.11, joga=24.14, setas=26.86,
         p3=27.78, desl=29.27, entrar=31.41, p4=33.69, deixa=34.90, morna=35.66, nem=36.46,
         pronto=38.59, olha=39.32, tras=40.6, aperta=42.08, ondul=45.54, se=46.55, abre=48.71, ligav=50.27,
         nunca=52.51, mao=53.65, fica=54.63, gord=55.29, salva=57.46, segue=60.50)
T_END = 62.6

# ------------------------------------------------------------ geometria
WS_Y0, WS_Y1 = 430, 1050
WS_POLY = [(150, WS_Y0), (930, WS_Y0), (1060, WS_Y1), (20, WS_Y1)]
KNOB_X = [165, 415, 665, 915]; KNOB_Y = 1450; KNOB_R = 95
NUMCOL = [GREEN, RED, YEL, BLUE]

def street_scene():
    w, h = W, WS_Y1 - WS_Y0
    s = Image.new("RGB", (w, h), (170, 196, 222)); d = ImageDraw.Draw(s)
    hz = int(h * 0.45)
    for i in range(9):                                            # prédios ao fundo
        x = 60 + i * 115; bh = int(rng.integers(90, 200))
        d.rectangle([x, hz - bh, x + 80, hz], fill=(132, 150, 172))
        for yy in range(hz - bh + 14, hz - 10, 26):
            for xx in range(x + 12, x + 70, 22): d.rectangle([xx, yy, xx + 10, yy + 12], fill=(186, 200, 216))
    d.rectangle([0, hz, w, h], fill=(96, 140, 84))
    d.polygon([(w * 0.47, hz), (w * 0.53, hz), (w * 0.95, h), (w * 0.05, h)], fill=(72, 74, 88))   # rua em perspectiva
    for k in range(6):
        y0 = hz + (h - hz) * (k / 6) ** 1.6; y1 = hz + (h - hz) * ((k + 0.5) / 6) ** 1.6
        d.polygon([(w / 2 - 2 - k, y0), (w / 2 + 2 + k, y0), (w / 2 + 4 + 2 * k, y1), (w / 2 - 4 - 2 * k, y1)], fill=YEL)
    for side in (-1, 1):                                          # árvores
        for k in range(5):
            x = w / 2 + side * (120 + k * 90); y = hz + 10 + k * 18; r = 22 + k * 8
            d.ellipse([x - r, y - 2 * r, x + r, y], fill=(70, 128, 70))
    cx, cy = w / 2, hz + 150                                      # carro da frente
    d.rounded_rectangle([cx - 110, cy - 70, cx + 110, cy + 40], 20, fill=(48, 56, 80))
    d.rounded_rectangle([cx - 80, cy - 110, cx + 80, cy - 60], 16, fill=(60, 70, 96))
    for sx in (-1, 1): d.rounded_rectangle([cx + sx * 85 - 22, cy - 40, cx + sx * 85 + 22, cy - 18], 6, fill=(240, 40, 40))
    d.rectangle([cx - 40, cy - 10, cx + 40, cy + 12], fill=(230, 230, 230))
    return s

CLEAR = street_scene()

def fogged(img):
    f = img.filter(ImageFilter.GaussianBlur(26))
    a = np.array(f).astype(np.float32) * 0.45 + np.array([215, 220, 226], np.float32) * 0.55
    # luzes borradas do carro da frente
    out = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
    glow = Image.new("RGBA", out.size, (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
    cx, cy = W / 2, int((WS_Y1 - WS_Y0) * 0.45) + 120
    for sx in (-1, 1): gd.ellipse([cx + sx * 85 - 50, cy - 50, cx + sx * 85 + 50, cy + 30], fill=(255, 80, 80, 150))
    out.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))
    d = ImageDraw.Draw(out)
    for _ in range(900):                                          # gotinhas
        x, y, r = rng.integers(0, W), rng.integers(0, out.height), int(rng.integers(2, 8))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(236, 240, 244, 210), outline=(180, 188, 198, 200))
    return out.convert("RGB")

FOG = fogged(CLEAR)
WS_H = WS_Y1 - WS_Y0
YN = (np.arange(WS_H) / (WS_H - 1))[:, None, None]

def windshield(f, smear=0.0, wipe=None):
    """f = 1 embaçado ... 0 limpo; limpa de baixo para cima."""
    front = 1 - f; thr = (1 - front) * 1.2 - 0.1
    a = np.clip((thr - YN) / 0.12 + 0.5, 0, 1)
    out = np.array(CLEAR, np.float32) * (1 - a) + np.array(FOG, np.float32) * a
    img = Image.fromarray(out.astype(np.uint8)).convert("RGBA")
    if smear > 0:                                                 # marcas de gordura (arco da mão)
        ov = Image.new("RGBA", img.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        for k in range(4):
            od.arc([200 + k * 30, 120 + k * 26, 860 - k * 30, 760 - k * 26], 200, 340, fill=(250, 250, 250, int(150 * smear)), width=16)
        img.alpha_composite(ov.filter(ImageFilter.GaussianBlur(3)))
    if wipe is not None:                                          # faixa limpa onde a mão passou
        p = wipe; ov = Image.new("L", img.size, 0); od = ImageDraw.Draw(ov)
        od.arc([200, 120, 860, 760], 200, 200 + 140 * p, fill=255, width=120)
        img = Image.composite(CLEAR.convert("RGBA"), img, ov.filter(ImageFilter.GaussianBlur(10)))
    return img

def ws_mask():
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(WS_POLY, fill=255)
    return m.filter(ImageFilter.GaussianBlur(1))
WS_MASK = ws_mask()

def static_interior():
    c = paper_texture(W, H, PAPER, 6).convert("RGBA"); d = ImageDraw.Draw(c)
    d.rectangle([0, WS_Y0 - 70, W, 1230], fill=(62, 60, 66))                 # teto e colunas
    d.rectangle([0, WS_Y1 - 10, W, 1230], fill=(44, 44, 48))                 # painel
    d.ellipse([-120, WS_Y1 + 20, 620, 1600], outline=(28, 28, 30), width=46)  # volante
    d.rounded_rectangle([30, 1240, 1050, 1640], 46, fill=(30, 30, 34))       # console do ar
    d.rounded_rectangle([40, 1250, 1040, 1630], 40, outline=(70, 70, 76), width=4)
    return c
INTERIOR = static_interior()

def knob(c, i, led_on, t, extra=None):
    d = ImageDraw.Draw(c); x, y, r = KNOB_X[i], KNOB_Y, KNOB_R
    d.ellipse([x - r - 10, y - r - 10, x + r + 10, y + r + 10], fill=(52, 52, 58))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(18, 18, 20), outline=(190, 190, 196), width=8)
    d.rounded_rectangle([x - 22, y - 60, x + 22, y - 48], 5, fill=AMBER if led_on else (90, 90, 96))
    if led_on:
        g = Image.new("RGBA", (120, 80), (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse([20, 20, 100, 60], fill=AMBER + (120,))
        c.alpha_composite(g.filter(ImageFilter.GaussianBlur(10)), (x - 60, y - 94))
    if i == 0:
        f = F(INTER, 54); w = d.textlength("A/C", font=f); d.text((x - w / 2, y - 16), "A/C", font=f, fill=WHITE)
    elif i == 1:                                                  # para-brisa com setas onduladas
        d.polygon([(x - 46, y + 40), (x + 46, y + 40), (x + 34, y - 6), (x - 34, y - 6)], outline=WHITE, width=5)
        for k in (-20, 0, 20):
            d.line([(x + k, y + 32), (x + k + 6, y + 18), (x + k, y + 4), (x + k + 4, y - 12)], fill=WHITE, width=4)
            d.polygon([(x + k - 7, y - 10), (x + k + 11, y - 10), (x + k + 4, y - 24)], fill=WHITE)
    elif i == 2:                                                  # recirculação: carro + seta circular
        d.rounded_rectangle([x - 48, y + 4, x + 48, y + 36], 10, outline=WHITE, width=5)
        d.line([(x - 30, y + 4), (x - 18, y - 16), (x + 22, y - 16), (x + 34, y + 4)], fill=WHITE, width=5)
        d.arc([x - 22, y - 8, x + 22, y + 30], 30, 330, fill=WHITE, width=4)
        d.polygon([(x + 16, y - 6), (x + 28, y + 2), (x + 14, y + 10)], fill=WHITE)
    elif i == 3:                                                  # temperatura: arco azul->vermelho + ponteiro
        ang = extra if extra is not None else -120
        d.arc([x - r + 16, y - r + 16, x + r - 16, y + r - 16], 140, 270, fill=BLUE, width=12)
        d.arc([x - r + 16, y - r + 16, x + r - 16, y + r - 16], 270, 40, fill=RED, width=12)
        a = math.radians(ang - 90)
        d.line([(x, y), (x + 52 * math.cos(a), y + 52 * math.sin(a))], fill=WHITE, width=10)
        d.ellipse([x - 12, y - 12, x + 12, y + 12], fill=WHITE)

LABELS = ["LIGADO", "PARA-BRISA", "RECIRC. OFF", "MORNA"]
STEP_T = [T["liga"], T["joga"], T["desl"], T["deixa"]]

def number_badge(c, i, s):
    if s <= 0: return
    x, y = KNOB_X[i] - 78, 1300; r = 36 * s; d = ImageDraw.Draw(c)
    d.ellipse([x - r, y - r, x + r, y + r], fill=NUMCOL[i], outline=WHITE, width=max(2, int(5 * s)))
    f = F(SB, max(8, int(48 * s))); txt = str(i + 1); w = d.textlength(txt, font=f)
    d.text((x - w / 2, y - 30 * s), txt, font=f, fill=WHITE if i != 2 else INK)

def airflow(c, t, a):
    if a <= 0: return
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for k in range(7):
        x = 120 + k * 140
        for j in range(3):
            ph = ((t * 0.9 + j / 3 + k * 0.13) % 1.0)
            y = WS_Y1 - 20 - ph * 420; al = int(200 * a * math.sin(math.pi * ph))
            pts = [(x + 14 * math.sin((y - yy) / 20 + t * 4), yy) for yy in range(int(y), int(y) + 70, 7)]
            d.line(pts, fill=(255, 255, 255, al), width=7)
    c.alpha_composite(ov)

def vapor(c, t, a):
    if a <= 0: return
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for k in range(26):
        ph = (t * 0.35 + k * 0.137) % 1.0; x = 80 + (k * 211) % 920 + 20 * math.sin(t * 2 + k)
        y = 1150 - ph * 600; r = 16 + 8 * math.sin(k)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(235, 245, 255, int(230 * a * (1 - ph * 0.5))), outline=(150, 190, 230, int(230 * a)), width=3)
    c.alpha_composite(ov.filter(ImageFilter.GaussianBlur(2)))

def card_popup(c, t, t0, t1, draw):
    if not (t0 <= t < t1): return
    s = pop(t, t0, 0.3); a = 1 - prog(t, t1 - 0.25, t1)
    card = Image.new("RGBA", (860, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, 859, 519], 32, fill=CARD, outline=(210, 196, 166), width=6)
    draw(card, d)
    paste_scaled(c, card, (540, 740), s, a)

def rear_card(card, d, t):
    x0, y0 = 150, 90
    d.rounded_rectangle([x0, y0, x0 + 560, y0 + 300], 60, fill=(200, 214, 228), outline=INK, width=8)
    p = ease_out(prog(t, T["aperta"] + 0.3, T["ondul"]))
    for k in range(7):
        y = y0 + 50 + k * 34; col = (int(120 + 135 * p), int(120 - 40 * p), int(120 - 80 * p))
        d.line([(x0 + 40, y), (x0 + 520, y)], fill=col, width=5)
    d.text((x0 + 130, y0 + 330), "vidro de trás", font=F(SB, 50), fill=INK)

def nowin_card(card, d, t):
    x0, y0 = 120, 70
    d.polygon([(x0, y0 + 320), (x0 + 40, y0 + 60), (x0 + 360, y0 + 20), (x0 + 380, y0 + 320)], fill=(62, 60, 66))
    low = 70 * ease_out(prog(t, T["abre"], T["abre"] + 0.6))
    d.polygon([(x0 + 30, y0 + 310), (x0 + 60, y0 + 80 + low), (x0 + 345, y0 + 45 + low), (x0 + 360, y0 + 310)], fill=(190, 210, 228))
    if low > 5:
        for k in range(3):
            yy = y0 + 70 + k * 20; ph = (t * 1.5 + k * 0.3) % 1
            d.line([(x0 + 400 + ph * 60, yy), (x0 + 330 + ph * 60, yy)], fill=(90, 140, 200), width=6)
    if t >= T["ligav"]:                                           # ventilador
        fx, fy = 640, 200; s = pop(t, T["ligav"], 0.3); a0 = t * 400
        for k in range(4):
            a = math.radians(a0 + k * 90)
            d.ellipse([fx + 60 * s * math.cos(a) - 34 * s, fy + 60 * s * math.sin(a) - 34 * s, fx + 60 * s * math.cos(a) + 34 * s, fy + 60 * s * math.sin(a) + 34 * s], fill=BLUE)
        d.ellipse([fx - 20, fy - 20, fx + 20, fy + 20], fill=INK)
    d.text((x0 + 10, y0 + 360), "sem ar-condicionado?", font=F(SB, 52), fill=INK)

def hand(c, x, y, rot=0, s=1.0):
    h = Image.new("RGBA", (260, 320), (0, 0, 0, 0)); d = ImageDraw.Draw(h)
    skin = (226, 176, 138)
    d.rounded_rectangle([50, 120, 210, 300], 60, fill=skin, outline=(150, 100, 70), width=5)
    for k, (fx, fl) in enumerate([(58, 110), (98, 140), (138, 130), (178, 100)]):
        d.rounded_rectangle([fx - 18, 140 - fl, fx + 18, 170], 18, fill=skin, outline=(150, 100, 70), width=5)
    d.rounded_rectangle([190, 170, 250, 230], 26, fill=skin, outline=(150, 100, 70), width=5)
    paste_scaled(c, h.rotate(rot, expand=True, resample=Image.BICUBIC), (x, y), s)

def fog_level(t):
    if t < T["liga"]: return 1.0
    if t < T["joga"]: return 1 - 0.18 * ease_out(prog(t, T["liga"], T["joga"]))
    if t < T["desl"]: return 0.82 - 0.22 * ease_out(prog(t, T["joga"], T["desl"]))
    if t < T["deixa"]: return 0.60 - 0.20 * ease_out(prog(t, T["desl"], T["deixa"]))
    if t < T["pronto"]: return 0.40 - 0.15 * ease_out(prog(t, T["deixa"], T["pronto"]))
    if t < T["nunca"] - 0.4: return 0.25 * (1 - ease_io(prog(t, T["pronto"], T["olha"] + 1.4)))
    if t < T["fica"]: return ease_io(prog(t, T["nunca"] - 0.4, T["nunca"]))
    return 1.0

STAMPS = {"NAO": stamp_img("NÃO!", RED, size=150), "LIMPO": stamp_img("VIDRO LIMPO", GREEN, size=90, rot=6)}

def top_card(c):
    d = ImageDraw.Draw(c)
    d.rectangle([40, 200, 1040, 336], fill=CARD); d.rectangle([40, 332, 1040, 336], fill=(210, 196, 166))
    f = F(SB, 46); t = "COMO DESEMBAÇAR O PARA-BRISA"; d.text(((W - d.textlength(t, font=f)) / 2, 222), t, font=f, fill=INK)
    f2 = F(SB, 26); h = "@INSTRUTORGUSTAVOVIEIRA"; d.text(((W - d.textlength(h, font=f2)) / 2, 288), h, font=f2, fill=(120, 108, 90))

def lower(c, t, text, t0, t1, bg, fg=WHITE, rot=-2, y=1160, size=60, **kw):
    if t0 <= t < t1 + 0.2:
        a, dy = slide_in(t, t0, t1); paste_scaled(c, tag(text, size, bg, fg, rot, **kw), (540, y + dy), 1, a)

def frame(t):
    c = INTERIOR.copy()
    # para-brisa
    wipe = None; smear = 0.0
    if T["nunca"] + 0.2 <= t < T["fica"]: wipe = ease_io(prog(t, T["nunca"] + 0.3, T["mao"] + 0.5))
    if t >= T["fica"]: smear = ease_out(prog(t, T["fica"], T["gord"] + 0.3))
    ws = windshield(fog_level(t), smear, wipe)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.paste(ws, (0, WS_Y0))
    c.paste(layer, (0, 0), WS_MASK)
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([430, WS_Y0 + 12, 650, WS_Y0 + 84], 22, fill=(36, 36, 40)); d.rectangle([534, WS_Y0 - 20, 546, WS_Y0 + 14], fill=(36, 36, 40))
    if T["prim"] <= t < T["p1"]: vapor(c, t, ease_out(prog(t, T["umid"], T["umid"] + 0.5)) * (1 - prog(t, T["p1"] - 0.4, T["p1"])))
    if T["joga"] <= t < T["olha"] + 1.4: airflow(c, t, ease_out(prog(t, T["joga"], T["joga"] + 0.5)) * (1 - prog(t, T["olha"] + 1.0, T["olha"] + 1.4)))
    # painel do ar
    temp = -120 + 100 * ease_io(prog(t, T["deixa"], T["morna"] + 0.4))
    for i in range(4):
        on = t >= STEP_T[i] if i != 2 else t < STEP_T[2]        # recirculação começa ligada e é desligada
        if i == 3: on = False
        knob(c, i, on, t, temp if i == 3 else None)
        number_badge(c, i, pop(t, STEP_T[i] - 0.9, 0.3))
        if t >= STEP_T[i]:
            f = F(INTER, 30); txt = LABELS[i]; w = d.textlength(txt, font=f)
            d.text((KNOB_X[i] - w / 2, 1572), txt, font=f, fill=(235, 235, 235))
    for i, t0 in enumerate(STEP_T):                               # anel destacando o botão da vez
        t1 = STEP_T[i + 1] - 0.9 if i < 3 else T["pronto"]
        if t0 - 0.9 <= t < t1:
            p = ease_out(prog(t, t0 - 0.9, t0 - 0.5)); r = KNOB_R + 26 + 10 * math.sin(t * 6)
            d.ellipse([KNOB_X[i] - r, KNOB_Y - r, KNOB_X[i] + r, KNOB_Y + r], outline=NUMCOL[i] + (int(255 * p),), width=8)
    top_card(c)
    # textos
    if t < T["prim"]:
        paste_scaled(c, tag("vidro embaçou na chuva?", 70, WHITE, INK, 2), (540, 560), pop(t, 0.05, 0.3), 1 - prog(t, T["prim"] - 0.2, T["prim"]))
        paste_scaled(c, tag("não enxerga NADA?", 84, RED, WHITE, -2), (540, 690), pop(t, 1.82, 0.3), 1 - prog(t, T["prim"] - 0.2, T["prim"]))
        lower(c, t, "faz isso que limpa em segundos", T["faz"], T["prim"], GREEN, size=58)
    lower(c, t, "por que embaça?", T["prim"], T["umid"], NAVY, size=72)
    lower(c, t, "umidade de dentro do carro", T["umid"], T["frio"], NAVY, size=60)
    lower(c, t, "+ vidro frio = gotinhas", T["frio"], T["entao"], ORANGE, INK, size=64)
    lower(c, t, "o segredo: tirar a UMIDADE do ar", T["entao"], T["p1"], GREEN, size=56)
    for i, (txt, t0, t1) in enumerate([("PASSO 1 · liga o A/C", T["p1"], T["ele"]), ("o A/C seca o ar", T["ele"], T["mesmo"]),
                                         ("mesmo no frio, pode ligar", T["mesmo"], T["p2"]), ("PASSO 2 · ar no para-brisa", T["p2"], T["setas"]),
                                         ("o botão com as setinhas", T["setas"], T["p3"]), ("PASSO 3 · recirculação OFF", T["p3"], T["entrar"]),
                                         ("entra o ar de fora, mais seco", T["entrar"], T["p4"]), ("PASSO 4 · temperatura morna", T["p4"], T["nem"]),
                                         ("nem fria, nem quente", T["nem"], T["pronto"])]):
        col = NUMCOL[[0, 0, 0, 1, 1, 2, 2, 3, 3][i]]
        fg = INK if col == YEL else WHITE
        lower(c, t, txt, t0, t1, col if txt.startswith("PASSO") else NAVY, fg if txt.startswith("PASSO") else WHITE, size=60 if txt.startswith("PASSO") else 56, rot=-2 if i % 2 == 0 else 2)
    if T["pronto"] <= t < T["tras"]:
        sc, sh = stamp(t, T["pronto"]); paste_scaled(c, STAMPS["LIMPO"], (540 + sh, 640), sc, 1 - prog(t, T["tras"] - 0.2, T["tras"]))
        lower(c, t, "pronto! olha o vidro limpando", T["olha"], T["tras"], GREEN, size=58)
    card_popup(c, t, T["tras"], T["se"], lambda card, dd: rear_card(card, dd, t))
    lower(c, t, "botão do desembaçador TRASEIRO", T["aperta"], T["se"], NAVY, size=54)
    card_popup(c, t, T["se"], T["nunca"] - 0.3, lambda card, dd: nowin_card(card, dd, t))
    lower(c, t, "abre um pouquinho as janelas", T["abre"], T["ligav"], NAVY, size=58)
    lower(c, t, "+ ventilação no para-brisa", T["ligav"], T["nunca"] - 0.3, NAVY, rot=2, size=58)
    if T["nunca"] + 0.2 <= t < T["salva"]:
        p = ease_io(prog(t, T["nunca"] + 0.3, T["mao"] + 0.5)); a = math.radians(200 + 140 * p)
        hx = 530 + 330 * math.cos(a); hy = WS_Y0 + 440 + 320 * math.sin(a)
        if t < T["fica"] + 0.4: hand(c, hx, hy, -10 + 30 * p, 1.0)
        lower(c, t, "nunca passe a mão no vidro", T["nunca"], T["fica"], RED, size=58)
        lower(c, t, "marca de gordura = embaça MAIS", T["fica"], T["salva"], RED, rot=2, size=56)
        if t >= T["mao"]:
            sc, sh = stamp(t, T["mao"]); paste_scaled(c, STAMPS["NAO"], (790 + sh, 600), sc, 1 - prog(t, T["salva"] - 0.2, T["salva"]))
    # final
    if t >= T["salva"]:
        a = ease_out(prog(t, T["salva"], T["salva"] + 0.3)); c.alpha_composite(Image.new("RGBA", (W, H), PAPER + (int(235 * a),)))
        if t < T["segue"]:
            s = pop(t, T["salva"], 0.35); bounce = abs(math.sin((t - T["salva"]) * 5)) * 30 if t > T["salva"] + 0.4 else 0
            icon = Image.new("RGBA", (260, 320), (0, 0, 0, 0)); ImageDraw.Draw(icon).polygon([(30, 20), (230, 20), (230, 300), (130, 220), (30, 300)], fill=YEL, outline=INK, width=10)
            paste_scaled(c, icon, (540, 760 - bounce), s)
            paste_scaled(c, tag("SALVA esse vídeo", 90, NAVY, WHITE, -2), (540, 1060), pop(t, T["salva"] + 0.2, 0.3))
            paste_scaled(c, tag("pro próximo dia de chuva", 64, WHITE, INK, 2), (540, 1200), pop(t, T["salva"] + 1.2, 0.3))
        else:
            paste_scaled(c, tag("Me segue para mais", 74, NAVY, WHITE, -2), (540, 880), pop(t, T["segue"], 0.3))
            paste_scaled(c, tag("dicas de trânsito", 92, YEL, INK, 2), (540, 1020), pop(t, T["segue"] + 0.35, 0.3))
            q = ease_out(prog(t, T["segue"] + 0.7, T["segue"] + 1.0))
            if q > 0: paste_scaled(c, tag("@instrutorgustavovieira", 52, WHITE, INK, 0, font=INTER), (540, 1200 + (1 - q) * 30), 1, q)
    return c.convert("RGB")

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
