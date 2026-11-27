"""Semijoias separadas por faixa de valor — visual sóbrio (preto, dourado champanhe, marfim), muito movimento.
Cortes no tempo da batida (96 bpm). Sem marca: só "Semijoias".
Uso: semijoias_valores.py - [PREVIEW_DIR]   (sem preview: frames RGB24 1080x1920@30 em stdout)
Env: PREV_TS=1,2,...  DUR_ONLY=1  BEATS_ONLY=1"""
import sys, os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(R, "assets"); FD = os.path.join(A, "fonts"); PD = os.path.join(A, "semijoias", "pecas")
PREVIEW = sys.argv[2] if len(sys.argv) > 2 else None
W, H, FPS = 1080, 1920, 30
BPM = 96; B = 60 / BPM

BG = (14, 13, 12); BG2 = (22, 20, 18); GOLD = (200, 166, 104); GOLD_L = (226, 200, 150)
IVORY = (238, 232, 222); GRAY = (146, 138, 126); LINE = (60, 56, 50)

def serif(s, w=500): return ImageFont.truetype(f"{FD}/Cormorant-{w}.ttf", s)
def sans(s, w="Regular"): return ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", s)

# ---------- dados ----------
TIERS = [
 dict(top="ATÉ", big="R$ 30", label="ATÉ R$ 30", sub="Pontos de luz, pérolas e delicados", items=[
   ("11058", "Brinco Pérola Mini", "Prata banhada", 17.90),
   ("11945", "Ponto de Luz", "Aço inox", 19.90),
   ("11953", "Brinco Quadrado Cravejado", "Prata banhada", 29.90)]),
 dict(top="DE R$ 30 ATÉ", big="R$ 70", label="R$ 30 – R$ 70", sub="Argolas, gotas e trios", items=[
   ("11813", "Argola Cravejada", "Prata banhada", 49.90),
   ("11061", "Trio Esmeralda", "Prata banhada", 59.90),
   ("12149", "Brinco Gota", "Aço inox", 69.90)]),
 dict(top="DE R$ 70 ATÉ", big="R$ 150", label="R$ 70 – R$ 150", sub="Anéis, conjuntos e pulseiras", items=[
   ("11896", "Anel Tri Zircônia", "Aço inox dourado", 79.90),
   ("11930", "Pulseira Zircônia", "Banho italiano", 119.90),
   ("11729", "Conjunto Gota Esmeralda", "Colar + brinco", 129.90)]),
 dict(top="ACIMA DE", big="R$ 150", label="ACIMA DE R$ 150", sub="Correntes, rivieras e relógios", items=[
   ("11619", "Corrente Gravata", "Semijoia dourada", 189.90),
   ("11676", "Corrente Riviera", "Semijoia dourada", 199.90),
   ("11546", "Relógio Libélula", "Prata e preto", 279.90)]),
]
WALL = ["11985", "12042", "11752", "11054", "11690", "11810", "11672", "11866", "11637", "12154", "11806", "9360",
        "11743", "12106", "11703", "11651", "11071", "11896", "11729", "11546", "11930", "11619", "11676", "11813"]

# ---------- linha do tempo (em batidas) ----------
scenes = []
def add(kind, beats, **kw): scenes.append(dict(kind=kind, beats=beats, **kw))
add("intro", 6)
for ti, T in enumerate(TIERS):
    add("tier", 3, tier=ti, trans="wipe")
    for k, it in enumerate(T["items"]): add("prod", 3, tier=ti, k=k, item=it, trans="push" if k else "rise")
add("outro", 8, trans="wipe")
t = 0.0
for s in scenes: s["t0"] = t; t += s["beats"] * B; s["t1"] = t
DUR = round(t, 3)
if os.environ.get("DUR_ONLY"): print(DUR); sys.exit(0)

# ---------- utilidades ----------
LN = ["lnum"]
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def ease_io(x): x = min(max(x, 0), 1); return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
def alpha(im, k):
    if k >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * k))); return im
def txt(text, font, fill, track=0):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = sum(d.textlength(c, font=font, features=LN) for c in text) + track * max(len(text) - 1, 0)
    asc, desc = font.getmetrics()
    im = Image.new("RGBA", (int(w) + 8, asc + desc + 8), (0, 0, 0, 0)); dd = ImageDraw.Draw(im); x = 4
    for c in text: dd.text((x, 4), c, font=font, fill=fill + (255,), features=LN); x += d.textlength(c, font=font, features=LN) + track
    return im
def reveal(fr, im, x, y, p, a=1.0):
    """texto sobe de trás de uma linha invisível (máscara)."""
    p = ease(p)
    if p <= 0: return
    h = im.height; off = int((1 - p) * h)
    part = im.crop((0, 0, im.width, h - off))
    if part.height > 0: fr.alpha_composite(alpha(part, a), (int(x), int(y + off)))
def fmt(v): return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

_photo = {}
def photo(code, size):
    key = (code, size)
    if key not in _photo:
        ph = Image.open(os.path.join(PD, f"{code}.png")).convert("RGB")
        s = int(min(ph.size) * 0.80); x0 = int((ph.width - s) * 0.32); y0 = int((ph.height - s) * 0.30)
        ph = ph.crop((x0, y0, x0 + s, y0 + s)).resize((size, size), Image.LANCZOS)
        _photo[key] = ImageEnhance.Contrast(ph).enhance(1.04)
    return _photo[key]
def zoomed(img, z, box, cx=0.5, cy=0.5):
    """recorta img com zoom z (>=1) e redimensiona para box=(w,h)."""
    w, h = img.size; cw, ch = w / z, h / z
    x0 = (w - cw) * cx; y0 = (h - ch) * cy
    return img.resize(box, Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))

def base_bg():
    g = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / (H - 1); g.putpixel((0, y), tuple(int(BG[i] + (BG2[i] - BG[i]) * math.sin(k * math.pi)) for i in range(3)))
    im = g.resize((W, H))
    noise = Image.effect_noise((W // 2, H // 2), 30).resize((W, H)).filter(ImageFilter.GaussianBlur(0.6))
    return Image.blend(im, Image.merge("RGB", [noise] * 3), 0.025).convert("RGBA")
BGIMG = base_bg()

# vinheta (para fundos com foto)
def make_vignette():
    v = Image.new("L", (W // 4, H // 4), 0); d = ImageDraw.Draw(v)
    for i in range(60):
        k = i / 60; d.rounded_rectangle((k * 60, k * 110, W // 4 - k * 60, H // 4 - k * 110), radius=40, fill=int(255 * k ** 1.5))
    v = v.filter(ImageFilter.GaussianBlur(18)).resize((W, H))
    dark = Image.new("RGBA", (W, H), BG + (255,)); dark.putalpha(v.point(lambda x: 255 - x)); return dark
VIGN = make_vignette()
def make_band(y0=600, y1=1290):
    m = Image.new("L", (1, H), 0)
    for y in range(H):
        k = 1 - min(1, max(0, (abs(y - (y0 + y1) / 2) - (y1 - y0) / 2 + 160) / 160))
        m.putpixel((0, y), int(225 * k))
    b = Image.new("RGBA", (W, H), BG + (255,)); b.putalpha(m.resize((W, H))); return b
BAND = make_band()
# reflexo de luz diagonal (passa uma vez sobre a foto)
def make_shine(S):
    g = Image.new("L", (S * 3, S), 0); d = ImageDraw.Draw(g)
    for i in range(160): d.line((S + i * 1.2, 0, S + i * 1.2 - S * 0.5, S), fill=int(70 * math.sin(math.pi * i / 160)), width=3)
    return g.filter(ImageFilter.GaussianBlur(6))

# parede de fotos rolando (3 colunas em velocidades opostas)
TW = 344; GAP = 14; X0 = (W - 3 * TW - 2 * GAP) // 2
def make_strip(codes):
    st = Image.new("RGB", (TW, len(codes) * (TW + GAP)), BG)
    for k, c in enumerate(codes): st.paste(photo(c, TW), (0, k * (TW + GAP)))
    return st
STRIPS = [make_strip(WALL[i::3] * 2) for i in range(3)]
def wall(t, dim=0.38, speed=70):
    im = Image.new("RGB", (W, H), BG)
    for i, st in enumerate(STRIPS):
        L = st.height // 2; dirn = 1 if i % 2 == 0 else -1
        off = (200 + dirn * t * speed * (1.0 + 0.25 * i)) % L
        im.paste(st.crop((0, int(off), TW, int(off) + H)), (X0 + i * (TW + GAP), 0))
    im = ImageEnhance.Brightness(im).enhance(dim).convert("RGBA")
    im.alpha_composite(VIGN); return im

# ---------- cenas ----------
F_KICK = sans(26, "Medium"); F_SMALL = sans(30, "Regular"); F_NAME = serif(86, 600); F_PRICE = serif(150, 600)
F_RS = serif(60, 500)

def intro(lt):
    fr = wall(lt + 0.0, dim=0.32 + 0.1 * ease(lt / 1.5)); cx = W / 2
    # zoom de entrada
    z = 1.12 - 0.12 * ease(lt / 2.0)
    if z > 1.001: fr = zoomed(fr, z, (W, H))
    fr.alpha_composite(alpha(BAND, ease((lt - 0.2) / 0.6)))
    k = txt("COLEÇÃO", F_KICK, GOLD, 14); reveal(fr, k, cx - k.width / 2, 700, (lt - 0.3) / 0.5)
    word = "Semijoias"; f = serif(210, 600); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    wtot = d.textlength(word, font=f, features=LN); x = cx - wtot / 2
    for i, c in enumerate(word):
        ci = txt(c, f, IVORY); reveal(fr, ci, x - 4, 760, (lt - 0.5 - i * 0.06) / 0.55); x += d.textlength(c, font=f, features=LN)
    p = ease_io((lt - 1.2) / 0.8)
    if p > 0: ImageDraw.Draw(fr).line((cx - 230 * p, 1040, cx + 230 * p, 1040), fill=GOLD + (255,), width=2)
    s = txt("SEPARADAS POR VALOR", sans(34, "Medium"), IVORY, 10); reveal(fr, s, cx - s.width / 2, 1080, (lt - 1.6) / 0.5)
    s2 = txt("de R$ 17,90 a R$ 279,90", serif(52, 500), GOLD_L); reveal(fr, s2, cx - s2.width / 2, 1150, (lt - 2.1) / 0.5)
    return fr

_tierbg = {}
def tier_scene(s, lt):
    T = TIERS[s["tier"]]
    if s["tier"] not in _tierbg:
        ph = photo(T["items"][0][0], 1080).resize((1920, 1920), Image.LANCZOS).crop((420, 0, 1500, 1920))
        ph = ImageEnhance.Brightness(ph.filter(ImageFilter.GaussianBlur(14))).enhance(0.30).convert("RGBA")
        ph.alpha_composite(VIGN); _tierbg[s["tier"]] = ph
    fr = zoomed(_tierbg[s["tier"]], 1.0 + 0.06 * lt / (s["beats"] * B), (W, H))
    cx = W / 2
    n = txt(f"FAIXA {s['tier'] + 1} DE {len(TIERS)}", F_KICK, GOLD, 12); reveal(fr, n, cx - n.width / 2, 560, (lt - 0.05) / 0.4)
    top = txt(T["top"], sans(44, "Medium"), IVORY, 12); reveal(fr, top, cx - top.width / 2, 700, (lt - 0.15) / 0.45)
    # valor grande: dígitos rolando até o número final
    big = T["big"]; f = serif(250, 600); d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    wtot = d.textlength(big, font=f, features=LN); x = cx - wtot / 2
    for i, c in enumerate(big):
        cw = d.textlength(c, font=f, features=LN); p = (lt - 0.25 - i * 0.05) / 0.5
        if c.isdigit() and 0 < p < 1:
            roll = int((1 - ease(p)) * 12)
            c2 = str((int(c) + roll) % 10)
        else: c2 = c
        reveal(fr, txt(c2, f, IVORY), x - 4, 770, p); x += cw
    p = ease_io((lt - 0.7) / 0.7)
    if p > 0: ImageDraw.Draw(fr).line((cx - 300 * p, 1100, cx + 300 * p, 1100), fill=GOLD + (255,), width=2)
    sb = txt(T["sub"], serif(52, 500), GOLD_L); reveal(fr, sb, cx - sb.width / 2, 1140, (lt - 0.95) / 0.5)
    return fr

PX, PY, PS = 90, 300, 900
SHINE = make_shine(PS)
def prod_scene(s, lt):
    fr = BGIMG.copy(); T = TIERS[s["tier"]]; code, name, mat, price = s["item"]; dur = s["beats"] * B
    d = ImageDraw.Draw(fr)
    # foto: zoom-out lento + leve deriva
    ph = photo(code, 1080)
    z = 1.16 - 0.12 * ease(lt / dur * 1.2)
    img = zoomed(ph, z, (PS, PS), 0.5 + 0.03 * math.sin(lt), 0.5)
    sp = (lt - 0.55) / 0.9
    if 0 < sp < 1:
        m = SHINE.crop((int(2 * PS * (1 - sp)), 0, int(2 * PS * (1 - sp)) + PS, PS))
        img = Image.composite(Image.new("RGB", (PS, PS), (255, 248, 235)), img, m)
    fr.paste(img, (PX, PY))
    # moldura dourada fina que se desenha
    p = ease_io((lt - 0.1) / 0.7); o = 16
    if p > 0:
        x0, y0, x1, y1 = PX - o, PY - o, PX + PS + o, PY + PS + o
        per = 2 * (x1 - x0) + 2 * (y1 - y0); L = per * p
        segs = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
        for a, b in segs:
            sl = math.hypot(b[0] - a[0], b[1] - a[1])
            if L <= 0: break
            k = min(1, L / sl); d.line((a, (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)), fill=GOLD + (255,), width=2); L -= sl
    # textos
    ix = txt(f"{s['k'] + 1:02d} / {len(T['items']):02d}", F_KICK, GOLD, 8); reveal(fr, ix, PX - 4, 1262, (lt - 0.1) / 0.4)
    nm = txt(name, F_NAME, IVORY); reveal(fr, nm, PX - 6, 1300, (lt - 0.18) / 0.45)
    mt = txt(mat.upper(), sans(26, "Medium"), GRAY, 6); reveal(fr, mt, PX - 4, 1410, (lt - 0.3) / 0.45)
    # preço contando
    q = ease((lt - 0.35) / 0.8); val = price * (0.6 + 0.4 * q) if q < 1 else price
    rs = txt("R$", F_RS, GOLD); pr = txt(fmt(val), F_PRICE, GOLD)
    reveal(fr, rs, PX - 4, 1530, (lt - 0.35) / 0.4); reveal(fr, pr, PX + rs.width + 4, 1478, (lt - 0.35) / 0.4)
    return fr

def outro(lt):
    fr = wall(lt + 9.0, dim=0.22, speed=55); cx = W / 2
    pnl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(pnl).rectangle((70, 470, W - 70, 1460), fill=BG + (215,))
    fr.alpha_composite(alpha(pnl, ease(lt / 0.5)))
    d = ImageDraw.Draw(fr)
    p = ease_io((lt - 0.1) / 0.8)
    if p > 0:
        x0, y0, x1, y1 = 70, 470, W - 70, 1460
        d.line((x0, y0, x0 + (x1 - x0) * p, y0), fill=GOLD + (255,), width=2); d.line((x1, y1, x1 - (x1 - x0) * p, y1), fill=GOLD + (255,), width=2)
    k = txt("ESCOLHA A SUA", F_KICK, GOLD, 14); reveal(fr, k, cx - k.width / 2, 560, (lt - 0.2) / 0.45)
    t1 = txt("Semijoias", serif(170, 600), IVORY); reveal(fr, t1, cx - t1.width / 2, 610, (lt - 0.3) / 0.5)
    for i, T in enumerate(TIERS):
        y = 880 + i * 82; pp = (lt - 0.7 - i * 0.18) / 0.45
        lab = txt(T["label"], sans(34, "Medium"), IVORY, 6); reveal(fr, lab, cx - lab.width / 2, y, pp)
        if i < 3 and ease(pp) > 0.5: d.line((cx - 30, y + 70, cx + 30, y + 70), fill=LINE + (255,), width=2)
    bp = ease((lt - 1.6) / 0.6)
    if bp > 0:
        bt = txt("ENCOMENDE PELO WHATSAPP", sans(30, "SemiBold"), BG, 6)
        bw, bh = bt.width + 90, 96; btn = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        ImageDraw.Draw(btn).rectangle((0, 0, bw - 1, bh - 1), fill=GOLD + (255,)); btn.alpha_composite(bt, (45, (bh - bt.height) // 2 + 2))
        fr.alpha_composite(alpha(btn, bp), (int(cx - bw / 2), int(1250 + (1 - bp) * 20)))
    pe = txt("PRONTA ENTREGA", F_KICK, GOLD, 14); reveal(fr, pe, cx - pe.width / 2, 1395, (lt - 2.0) / 0.45)
    return fr

def scene_frame(s, lt):
    return {"intro": lambda: intro(lt), "tier": lambda: tier_scene(s, lt), "prod": lambda: prod_scene(s, lt), "outro": lambda: outro(lt)}[s["kind"]]()

# ---------- sobreposições fixas ----------
HDR_L = txt("SEMIJOIAS", sans(24, "SemiBold"), IVORY, 10)
TIER_LBL = [txt(T["label"], sans(24, "SemiBold"), GOLD, 6) for T in TIERS]
def overlay(fr, t, s):
    if s["kind"] in ("tier", "prod"):
        fr.alpha_composite(HDR_L, (PX - 4, 150))
        lb = TIER_LBL[s["tier"]]; a = ease((t - s["t0"]) / 0.4) if s["kind"] == "tier" else 1
        fr.alpha_composite(alpha(lb, a), (W - PX - lb.width + 4, 150))
        d = ImageDraw.Draw(fr); y = 1820; gap = 10; segw = (W - 2 * PX - gap * 3) / 4
        for i in range(4):
            x = PX + i * (segw + gap); d.rectangle((x, y, x + segw, y + 3), fill=LINE + (255,))
            T0 = [sc for sc in scenes if sc.get("tier") == i]; a0, a1 = T0[0]["t0"], T0[-1]["t1"]
            p = min(max((t - a0) / (a1 - a0), 0), 1)
            if p > 0: d.rectangle((x, y, x + segw * p, y + 3), fill=GOLD + (255,))
    return fr

# ---------- transições ----------
XF = 0.42
def compose(t):
    i = max(k for k, s in enumerate(scenes) if s["t0"] <= t); s = scenes[i]; lt = t - s["t0"]
    cur = scene_frame(s, lt)
    if i > 0 and lt < XF:
        prv = scenes[i - 1]; old = scene_frame(prv, t - prv["t0"]); p = ease_io(lt / XF); tr = s.get("trans", "fade")
        if tr == "push":       # empurra para a esquerda
            fr = Image.new("RGBA", (W, H), BG + (255,))
            fr.alpha_composite(old, (int(-W * p), 0)); fr.alpha_composite(cur, (int(W * (1 - p)), 0)); cur = fr
        elif tr == "rise":     # nova cena sobe por cima
            fr = old.copy(); off = int(H * (1 - p)); fr.alpha_composite(cur.crop((0, 0, W, H - off)), (0, off))
            if 0 < off < H: ImageDraw.Draw(fr).line((0, off, W, off), fill=GOLD + (255,), width=3)
            cur = fr
        elif tr == "wipe":     # cortina da esquerda p/ direita com fio dourado
            fr = old.copy(); xw = int(W * p)
            if xw > 0: fr.alpha_composite(cur.crop((0, 0, xw, H)), (0, 0))
            if 0 < xw < W: ImageDraw.Draw(fr).line((xw, 0, xw, H), fill=GOLD + (255,), width=3)
            cur = fr
        else: cur = Image.blend(old, cur, p)
    return overlay(cur, t, s if not (i > 0 and lt < XF / 2) else scenes[i - 1])

out = sys.stdout.buffer
prev = [float(x) for x in os.environ.get("PREV_TS", "2.8,5.5,7.0,8.4,12.5,25,33.5,36.5").split(",")] if PREVIEW else None
for n in range(int(round(DUR * FPS))):
    t = n / FPS
    if PREVIEW and not any(abs(t - pt) < 0.5 / FPS for pt in prev): continue
    fr = compose(t)
    if n < 10: fr = Image.blend(Image.new("RGBA", (W, H), BG + (255,)), fr, n / 10)
    if DUR - t < 0.5: fr = Image.blend(Image.new("RGBA", (W, H), BG + (255,)), fr, max(0, (DUR - t) / 0.5))
    if PREVIEW: fr.convert("RGB").save(f"{PREVIEW}/s{t:05.2f}.png")
    else: out.write(fr.convert("RGB").tobytes())
