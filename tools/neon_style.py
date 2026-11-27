"""Hidragloss em estilo "motion neon" (fundo escuro, brilho rosa, card de app, chips, sigla G·L·O·W, lista que acende).
Sem pessoa em cena: a parte de baixo usa a foto dos lábios com zoom lento.
Uso: neon_style.py FONTS_DIR ASSETS_DIR - [PREVIEW_DIR]   (sem preview: frames RGB24 1080x1920@30 em stdout)
Env: PREV_TS=1,5,...   SFX_OUT=arquivo.json (salva os tempos dos efeitos sonoros)"""
import sys, os, math, random, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD, AD = sys.argv[1], sys.argv[2]; PREVIEW = sys.argv[4] if len(sys.argv) > 4 else None
W, H, FPS, DUR = 1080, 1920, 30, 35.5

BG = (10, 6, 9); ACC = (255, 105, 160); ACC2 = (255, 190, 214); WHITE = (246, 240, 243)
GRAY = (150, 136, 145); DIM = (88, 76, 84); CARD = (22, 16, 20); CARD2 = (30, 22, 27); EDGE = (64, 46, 56)

def F(name, size): return ImageFont.truetype(f"{FD}/{name}", size)
def PB(s): return F("Poppins-Bold.ttf", s)
def PS(s): return F("Poppins-SemiBold.ttf", s)
def PM(s): return F("Poppins-Medium.ttf", s)
def MONO(s): return F("SpaceMono-Bold.ttf", s)
def SER(s):
    f = F("PlayfairDisplay-Italic%5Bwght%5D.ttf", s)
    try: f.set_variation_by_axes([600])
    except Exception: pass
    return f

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0), 1); c = 1.6; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2
def alpha(im, k):
    if k >= 0.999: return im
    if k <= 0: return None
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * k))); return im

def text_img(t, font, fill, track=0):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(sum(d.textlength(c, font=font) + track for c in t) - track) + 8 if track else int(d.textlength(t, font=font)) + 8
    asc, desc = font.getmetrics(); im = Image.new("RGBA", (max(w, 1), asc + desc + 8), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    if track:
        x = 4
        for c in t: dd.text((x, 4), c, font=font, fill=fill + (255,)); x += d.textlength(c, font=font) + track
    else: dd.text((4, 4), t, font=font, fill=fill + (255,))
    return im
def gradient_text(t, font, top=(255, 200, 222), bot=(255, 84, 150)):
    m = text_img(t, font, (255, 255, 255)).getchannel("A"); w, h = m.size
    g = Image.new("RGBA", (1, h))
    for y in range(h):
        k = y / max(h - 1, 1); g.putpixel((0, y), tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3)) + (255,))
    g = g.resize((w, h)); g.putalpha(m); return g
def glow(im, color=ACC, r=22, strength=1.1, pad=None):
    pad = pad or r * 3; big = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); big.alpha_composite(im, (pad, pad))
    a = big.getchannel("A").filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * strength)))
    g = Image.new("RGBA", big.size, color + (0,)); g.putalpha(a)
    out = Image.new("RGBA", big.size, (0, 0, 0, 0)); out.alpha_composite(g); out.alpha_composite(big); return out
def put(fr, im, cx, cy, k=1.0, sc=1.0):
    if im is None or k <= 0: return
    if abs(sc - 1) > 0.002: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BICUBIC)
    im = alpha(im, k)
    if im is not None: fr.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))
def put_tl(fr, im, x, y, k=1.0):
    im = alpha(im, k)
    if im is not None: fr.alpha_composite(im, (int(x), int(y)))

# ---------- fundo ----------
def make_bg():
    im = Image.new("RGB", (W, H), BG); ov = Image.new("L", (W, H), 0); d = ImageDraw.Draw(ov)
    d.ellipse((W / 2 - 520, H * 0.42 - 520, W / 2 + 520, H * 0.42 + 520), fill=110); ov = ov.filter(ImageFilter.GaussianBlur(220))
    plum = Image.new("RGB", (W, H), (58, 18, 40)); im = Image.composite(plum, im, ov).convert("RGBA")
    d = ImageDraw.Draw(im); rnd = random.Random(5)
    for _ in range(90):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H); r = rnd.choice([1, 1, 1.5, 2]); a = rnd.randint(60, 170)
        c = rnd.choice([(255, 200, 225), (200, 180, 255), (255, 255, 255)])
        d.ellipse((x - r, y - r, x + r, y + r), fill=c + (a,))
    return im
BGI = make_bg()

# ---------- elementos fixos ----------
def ig_handle():
    im = Image.new("RGBA", (420, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x0 = 360
    d.rounded_rectangle((x0, 6, x0 + 46, 52), radius=13, outline=WHITE + (255,), width=4)
    d.ellipse((x0 + 12, 18, x0 + 34, 40), outline=WHITE + (255,), width=4); d.ellipse((x0 + 34, 11, x0 + 40, 17), fill=WHITE + (255,))
    t = text_img("@BRUNABORGESESTETIC", PS(24), WHITE); im.alpha_composite(t, (420 - t.width, 66)); return im
IG = ig_handle()
def kicker(t, color=(210, 188, 200)):
    tx = text_img(t.upper(), MONO(24), color, track=5); im = Image.new("RGBA", (tx.width + 34, tx.height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im); cy = tx.height // 2 + 1; d.ellipse((4, cy - 6, 16, cy + 6), fill=ACC + (255,)); im.alpha_composite(tx, (30, 0))
    return glow(im, ACC, 6, 0.5, pad=12)
def pill(t, font, fill, border, txt, dot=True, pad=(34, 16), glowc=None):
    tx = text_img(t, font, txt); w = tx.width + pad[0] * 2 + (26 if dot else 0); h = tx.height + pad[1] * 2 - 8
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=fill + (255,), outline=border + (255,) if border else None, width=2)
    x = pad[0]
    if dot: cy = h // 2; d.ellipse((x - 6, cy - 7, x + 8, cy + 7), fill=(ACC if fill != ACC else WHITE) + (255,)); x += 26
    im.alpha_composite(tx, (x, (h - tx.height) // 2 + 1))
    return glow(im, glowc, 16, 0.9, pad=30) if glowc else glow(im, (0, 0, 0), 1, 0, pad=30)

# ---------- foto dos lábios (parte de baixo, como o "vídeo" do modelo) ----------
PHOTO = Image.open(f"{AD}/hidragloss/labios_limpio.png").convert("RGB")
PH_Y, PH_H = 1120, 800
def photo_panel(fr, t, z0, z1, t0, t1, focus=(0.55, 0.5)):
    k = min(max((t - t0) / (t1 - t0), 0), 1); z = z0 + (z1 - z0) * k
    base_w = W * z; sc = base_w / PHOTO.width; bh = PHOTO.height * sc
    if bh < PH_H: sc = PH_H * z / PHOTO.height; base_w = PHOTO.width * sc; bh = PH_H * z
    img = PHOTO.resize((int(base_w), int(bh)), Image.BICUBIC)
    cx = (img.width - W) * focus[0]; cy = (img.height - PH_H) * focus[1]
    crop = img.crop((int(cx), int(cy), int(cx) + W, int(cy) + PH_H)).convert("RGBA")
    fr.alpha_composite(crop, (0, PH_Y))
    sh = Image.new("RGBA", (W, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    for i in range(60): d.line((0, i, W, i), fill=(0, 0, 0, int(120 * (1 - i / 60))))
    fr.alpha_composite(sh, (0, PH_Y))

SFX = []   # (tempo, tipo)
def sfx(t, kind): SFX.append((round(t, 3), kind))

# ---------- cenas ----------
# A: gancho
def icon_gloss():
    im = Image.new("RGBA", (200, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((50, 30, 150, 270), radius=34, outline=ACC2 + (255,), width=6, fill=(40, 14, 28, 255))
    d.rounded_rectangle((68, 150, 132, 250), radius=20, fill=ACC + (255,))
    d.rounded_rectangle((72, 40, 128, 112), radius=16, fill=(255, 160, 200, 255))
    pts = [(100 + r * math.cos(math.pi / 4 * i - math.pi / 2), 190 + r * math.sin(math.pi / 4 * i - math.pi / 2)) for i, r in enumerate([22, 6] * 4)]
    d.polygon(pts, fill=WHITE + (255,))
    return glow(im, ACC, 26, 1.2)
A_ICON = icon_gloss(); A_K = kicker("El secreto de unos labios perfectos"); A_S = glow(text_img("tiene nombre:", SER(74), WHITE), (255, 255, 255), 8, 0.35)
A_BIG = glow(gradient_text("Hidragloss", PB(178)), ACC, 34, 1.25)
BUB = [(random.Random(i).uniform(660, 980), random.Random(i + 50).uniform(0, 1), random.Random(i + 99).uniform(7, 24)) for i in range(14)]
def bubbles(fr, lt, t0=0.0, x_off=0, y_base=640):
    if lt < t0: return
    d = ImageDraw.Draw(fr)
    for x, ph, r in BUB:
        y = y_base - ((lt - t0) * 70 + ph * 380) % 420; x2 = x + x_off + math.sin(lt * 1.4 + ph * 6) * 12
        a = int(150 * min((lt - t0) / 0.6, 1) * (0.4 + 0.6 * (y - (y_base - 420)) / 420))
        if a > 0: d.ellipse((x2 - r, y - r, x2 + r, y + r), outline=(230, 220, 228, a), width=3)
def scene_A(fr, lt):
    put(fr, A_ICON, W / 2, 650, ease(lt / 0.5), 0.8 + 0.2 * back(lt / 0.5))
    bubbles(fr, lt, 1.2, y_base=440)
    put(fr, A_K, W / 2, 860, ease((lt - 0.3) / 0.4))
    put(fr, A_S, W / 2, 960, ease((lt - 0.6) / 0.4))
    p = (lt - 1.5) / 0.45; put(fr, A_BIG, W / 2, 1110, ease(p), 1.18 - 0.18 * back(p))
    put(fr, IG, W - 90 - 210, 500, ease((lt - 0.2) / 0.5))

# B: card de "app" + digitação + chip
TYPED = "mis labios: secos, sin brillo"
B_HEAD = kicker("BBLIPS · Diagnóstico", (215, 200, 208))
B_CHIP = pill("el secreto: hidratación profunda", PS(34), ACC, None, (255, 255, 255), glowc=ACC)
B_RESP = text_img("›  la solución: Hidragloss", PM(30), (200, 176, 188))
def card_base():
    im = Image.new("RGBA", (940, 430), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 939, 429), radius=34, fill=CARD + (245,), outline=EDGE + (255,), width=2)
    d.rounded_rectangle((30, 92, 909, 182), radius=20, fill=(30, 22, 27, 255), outline=(58, 42, 52, 255), width=2)
    d.text((54, 112), "›", font=MONO(40), fill=ACC + (255,))
    d.rounded_rectangle((834, 106, 896, 168), radius=16, fill=ACC + (255,))
    d.line((865, 152, 865, 122), fill=WHITE + (255,), width=5); d.line((852, 134, 865, 121, 878, 134), fill=WHITE + (255,), width=5, joint="curve")
    return im
B_CARD = card_base()
def scene_B(fr, lt, t):
    photo_panel(fr, t, 1.0, 1.10, 4.2, 16.6)
    p = ease(lt / 0.45); x0, y0 = 70, 330
    put_tl(fr, alpha(B_CARD, p), x0, y0 + (1 - p) * 30)
    if p > 0.3:
        fr.alpha_composite(alpha(B_HEAD, p), (x0 + 10, y0 + 6))
        n = int(len(TYPED) * min(max((lt - 0.7) / 1.8, 0), 1))
        tx = text_img(TYPED[:n] + ("▍" if (lt * 2.5) % 1 < 0.6 and n < len(TYPED) else ""), MONO(32), WHITE)
        fr.alpha_composite(tx, (x0 + 96, y0 + 115))
        q = ease((lt - 2.8) / 0.4)
        if q > 0:
            d = ImageDraw.Draw(fr); cx, cy = x0 + 70, y0 + 240
            d.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), fill=(60, 40, 52, int(255 * q)))
            d.ellipse((cx - 8, cy - 8, cx + 8, cy + 8), fill=ACC + (int(255 * q),))
            for i, wv in enumerate((720, 620, 460)):
                d.rounded_rectangle((x0 + 120, y0 + 220 + i * 34, x0 + 120 + wv * q, y0 + 238 + i * 34), radius=9, fill=(70, 58, 66, int(255 * q)))
        put_tl(fr, B_RESP, x0 + 120, y0 + 330, ease((lt - 3.4) / 0.4))
    q = (lt - 4.1) / 0.4
    if q > 0:
        c = B_CHIP.rotate(3, resample=Image.BICUBIC, expand=True); put(fr, c, x0 + 20 + c.width / 2 - 30, y0 + 445, ease(q), 0.85 + 0.15 * back(q))
    put(fr, IG, W - 90 - 210, PH_Y - 70, 1.0)

# C: chips em fluxo
ROWS = [("¿labios secos?", "hidratación profunda"), ("¿sin brillo?", "glow natural"),
        ("¿arruguitas?", "menos pliegues"), ("¿el paso del tiempo?", "estimula el colágeno")]
C_L = [pill(a, PM(32), CARD2, EDGE, (230, 220, 226)) for a, _ in ROWS]
C_R = [pill(b, PS(32), (40, 12, 28), ACC, ACC2, glowc=ACC) for _, b in ROWS]
C_K = kicker("Lo que hace por tus labios")
def scene_C(fr, lt, t):
    photo_panel(fr, t, 1.0, 1.10, 4.2, 16.6)
    put(fr, C_K, W / 2, 330, ease(lt / 0.4))
    d = ImageDraw.Draw(fr)
    for k in range(4):
        t0 = 0.4 + k * 1.35; y = 470 + k * 150
        pl = (lt - t0) / 0.35
        if pl <= 0: continue
        L = C_L[k]; lx = 70 - 30
        put_tl(fr, alpha(L, ease(pl)), lx, y - L.height / 2)
        ax0 = lx + L.width - 40; ax1 = ax0 + 95; pa = min(max((lt - t0 - 0.3) / 0.3, 0), 1)
        x = ax0
        while x < ax0 + (ax1 - ax0) * pa - 8:
            d.line((x, y, min(x + 10, ax1 - 14), y), fill=(200, 160, 180, 255), width=3); x += 18
        if pa >= 1: d.polygon([(ax1 - 14, y - 9), (ax1 + 2, y), (ax1 - 14, y + 9)], fill=(200, 160, 180, 255))
        pr = (lt - t0 - 0.6) / 0.35
        if pr > 0: R = C_R[k]; put(fr, R, ax1 - 20 + R.width / 2, y, ease(pr), 0.85 + 0.15 * back(pr))
    put(fr, IG, W - 90 - 210, PH_Y - 70, 1.0)

# D: card "cómo recordarlo"
def card_D():
    im = Image.new("RGBA", (680, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, 679, 399), radius=34, fill=CARD + (250,), outline=EDGE + (255,), width=2)
    k = kicker("Cómo recordarlo", (200, 186, 194)); im.alpha_composite(k, ((680 - k.width) // 2, 20))
    s = text_img("unos labios perfectos", SER(58), WHITE); im.alpha_composite(s, ((680 - s.width) // 2, 112))
    return im
D_CARD = card_D(); D_EQ = glow(gradient_text("= ?", PB(130)), ACC, 26, 1.2)
def scene_D(fr, lt):
    put(fr, D_CARD, W / 2, 900, ease(lt / 0.4), 0.9 + 0.1 * back(lt / 0.4))
    p = (lt - 0.8) / 0.4; pulse = 1 + 0.04 * math.sin(max(lt - 1.2, 0) * 5)
    put(fr, D_EQ, W / 2, 1010, ease(p), (0.7 + 0.3 * back(p)) * pulse)
    put(fr, IG, W - 90 - 210, 500, 1.0)

# E: sigla G·L·O·W
E_K = kicker("La fórmula"); E_L = [glow(gradient_text(c, PB(250)), ACC, 36, 1.25) for c in "GLOW"]
E_Q = text_img("¿qué significa?", SER(66), WHITE)
def scene_E(fr, lt):
    put(fr, E_K, W / 2, 740, ease(lt / 0.4))
    widths = [im.width - 216 for im in E_L]; total = sum(widths) - 40; x = W / 2 - total / 2
    for i, im in enumerate(E_L):
        p = (lt - 0.35 - i * 0.32) / 0.35
        put(fr, im, x + widths[i] / 2, 960, ease(p), 1.25 - 0.25 * back(p)); x += widths[i] - 13
    put(fr, E_Q, W / 2, 1160, ease((lt - 1.9) / 0.4))
    put(fr, IG, W - 90 - 210, 500, 1.0)

# F: lista que acende item a item
ITEMS = [("G", "Glow", "brillo y volumen natural"), ("L", "Lisos", "mejora la textura y las arruguitas"),
         ("O", "Óptima hidratación", "hidratación profunda"), ("W", "Wow", "estimula el colágeno y rejuvenece")]
def tile(letter, on):
    s = 118; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if on:
        g = Image.new("RGBA", (1, s))
        for y in range(s): k = y / (s - 1); g.putpixel((0, y), (int(255 - 20 * k), int(140 - 60 * k), int(190 - 30 * k), 255))
        g = g.resize((s, s)); m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, s - 1, s - 1), radius=28, fill=255); g.putalpha(m); im = g
    else: d.rounded_rectangle((0, 0, s - 1, s - 1), radius=28, fill=(28, 21, 26, 255), outline=(52, 40, 48, 255), width=2)
    tx = text_img(letter, PB(66), WHITE if on else (92, 80, 88)); im.alpha_composite(tx, ((s - tx.width) // 2, (s - tx.height) // 2 + 2))
    return glow(im, ACC, 24, 1.1, pad=40) if on else glow(im, (0, 0, 0), 1, 0, pad=40)
F_ROWS = []
for L, ti, su in ITEMS:
    F_ROWS.append(dict(on=tile(L, True), off=tile(L, False), t_on=text_img(ti, PB(60), WHITE), t_off=text_img(ti, PB(60), (96, 84, 92)),
                       s_on=text_img(su, PM(28), (215, 196, 206)), s_off=text_img(su, PM(28), (70, 60, 67))))
def scene_F(fr, lt, t):
    photo_panel(fr, t, 1.04, 1.12, 24.2, 31.5, focus=(0.35, 0.45))
    act = int(min(max((lt - 0.5) / 1.65, 0), 3.999))
    for i, r in enumerate(F_ROWS):
        y = 300 + i * 190; p = ease((lt - i * 0.12) / 0.4)
        if p <= 0: continue
        on = (lt >= 0.5 and i == act)
        put_tl(fr, alpha(r["on"] if on else r["off"], p), 90 - 40, y - 40)
        put_tl(fr, alpha(r["t_on"] if on else r["t_off"], p), 238, y - 2)
        put_tl(fr, alpha(r["s_on"] if on else r["s_off"], p), 242, y + 76)
    put(fr, IG, W - 90 - 210, PH_Y - 70, 1.0)

# G: final
m = Image.open(f"{AD}/logo_bblips_mask.png").getchannel("A"); lw = 500; m = m.resize((lw, int(m.height * lw / m.width)), Image.LANCZOS)
LOGO = Image.new("RGBA", m.size, WHITE + (255,)); LOGO.putalpha(m); LOGO = glow(LOGO, ACC, 22, 0.8)
G_P = pill("Reserva tu cita", PB(44), ACC, None, (255, 255, 255), dot=False, pad=(56, 24), glowc=ACC)
G_H = text_img("@BRUNABORGESESTETIC", MONO(28), (215, 196, 206), track=3); G_S = text_img("Bruna Borges · especialista en labios", SER(44), WHITE)
def scene_G(fr, lt):
    bubbles(fr, lt, 0.4, x_off=-300)
    put(fr, LOGO, W / 2, 700, ease(lt / 0.6), 0.92 + 0.08 * ease(lt / 0.6))
    put(fr, G_S, W / 2, 1040, ease((lt - 0.5) / 0.5))
    p = (lt - 0.9) / 0.4; put(fr, G_P, W / 2, 1180, ease(p), (0.8 + 0.2 * back(p)) * (1 + 0.02 * math.sin(max(lt - 1.4, 0) * 4)))
    put(fr, G_H, W / 2, 1320, ease((lt - 1.3) / 0.4))

SCENES = [(0.0, 4.2, "A"), (4.2, 10.3, "B"), (10.3, 16.6, "C"), (16.6, 20.3, "D"), (20.3, 24.2, "E"), (24.2, 31.5, "F"), (31.5, DUR, "G")]
def render_scene(name, t, t0):
    fr = BGI.copy(); lt = t - t0
    {"A": lambda: scene_A(fr, lt), "B": lambda: scene_B(fr, lt, t), "C": lambda: scene_C(fr, lt, t), "D": lambda: scene_D(fr, lt),
     "E": lambda: scene_E(fr, lt), "F": lambda: scene_F(fr, lt, t), "G": lambda: scene_G(fr, lt)}[name]()
    return fr

# efeitos sonoros (tempos)
sfx(1.5, "whoosh"); sfx(0.0, "pop")
for s0, _, n in SCENES[1:]: sfx(s0, "whoosh")
for i in range(26): sfx(4.2 + 0.7 + i * 1.8 / 26, "tick")
sfx(4.2 + 4.1, "pop")
for k in range(4): sfx(10.3 + 0.4 + k * 1.35, "pop"); sfx(10.3 + 1.0 + k * 1.35, "pop2")
sfx(16.6 + 0.8, "pop2")
for i in range(4): sfx(20.3 + 0.35 + i * 0.32, "pop")
for i in range(4): sfx(24.2 + 0.5 + i * 1.65, "pop2")
sfx(31.5 + 0.9, "pop2")
if os.environ.get("SFX_OUT"): json.dump(sorted(SFX), open(os.environ["SFX_OUT"], "w"))

XF = 0.28; out = sys.stdout.buffer
prev = [float(x) for x in os.environ.get("PREV_TS", "2.5,7.5,14,18.5,22.5,28,33.5").split(",")] if PREVIEW else None
for n in range(int(round(DUR * FPS))):
    t = n / FPS
    if PREVIEW and not any(abs(t - pt) < 0.5 / FPS for pt in prev): continue
    i = max(k for k, s in enumerate(SCENES) if s[0] <= t); s0, s1, nm = SCENES[i]
    fr = render_scene(nm, t, s0)
    if i > 0 and t - s0 < XF:
        p0, _, pn = SCENES[i - 1]; fr = Image.blend(render_scene(pn, t, p0), fr, ease((t - s0) / XF))
    if n < 6: fr = Image.blend(Image.new("RGBA", (W, H), BG + (255,)), fr, n / 6)
    if PREVIEW: fr.convert("RGB").save(f"{PREVIEW}/n{t:05.2f}.png")
    else: out.write(fr.convert("RGB").tobytes())
