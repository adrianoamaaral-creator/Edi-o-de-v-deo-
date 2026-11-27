"""Vídeo de semijoias Flor de Lótus — mesma pegada editorial dos vídeos BBLips
(título palavra por palavra, traço à mão, barras de progresso, cartela final), na identidade
da marca: preto + rosé, serifa Cormorant e assinatura em script.
Uso: flor_lotus.py - [PREVIEW_DIR]   (sem preview: escreve frames RGB24 1080x1920@30 em stdout)
Env: PREV_TS=1.5,4,...   DUR_ONLY=1 (só imprime a duração)"""
import sys, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(R, "assets"); FD = os.path.join(A, "fonts"); PD = os.path.join(A, "flor_lotus", "pecas")
PREVIEW = sys.argv[2] if len(sys.argv) > 2 else None
W, H, FPS = 1080, 1920, 30

# ---------- paleta Flor de Lótus ----------
ROSE = (214, 158, 146); ROSE_D = (176, 108, 96); ROSE_SOFT = (240, 214, 205)
BLUSH = (248, 241, 237); BLUSH2 = (242, 230, 224); INK = (34, 27, 27); GRAY = (124, 108, 104)
NOIR = (20, 16, 16); NOIR2 = (12, 10, 10); CREAM = (244, 234, 228)
LIGHT = dict(bg=(BLUSH, BLUSH2), ink=INK, gray=GRAY, accent=ROSE_D, base=(226, 210, 203), line=INK, soft=ROSE_SOFT)
DARK = dict(bg=(NOIR, NOIR2), ink=CREAM, gray=(184, 160, 152), accent=ROSE, base=(64, 52, 50), line=ROSE, soft=(58, 40, 38))

def serif(s, w=500): return ImageFont.truetype(f"{FD}/Cormorant-{w}.ttf", s)
def script(s): return ImageFont.truetype(f"{FD}/GreatVibes.ttf", s)
_INTER = "/usr/share/fonts/opentype/inter/Inter-{}.otf"
def sans(s, w="Regular"): return ImageFont.truetype(_INTER.format(w), s)

MX = 100
def background(th):
    c1, c2 = th["bg"]; g = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / (H - 1); g.putpixel((0, y), tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3)))
    im = g.resize((W, H))
    noise = Image.effect_noise((W // 2, H // 2), 40).resize((W, H)).filter(ImageFilter.GaussianBlur(0.6))
    return Image.blend(im, Image.merge("RGB", [noise] * 3), 0.03).convert("RGBA")

def header(th):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((MX, 120), "Flor de Lótus", font=script(58), fill=th["accent"] + (255,))
    f = sans(22, "Medium"); t = "SEMIJOIAS · ACESSÓRIOS"
    d.text((W - MX - d.textlength(t, font=f), 150), t, font=f, fill=th["gray"] + (255,))
    return im

# ---------- texto palavra por palavra ----------
def layout_words(text, f, x0, y0, lh, center=False):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1))); items = []; y = y0
    for line in text.split("\n"):
        x = (W - d.textlength(line, font=f)) / 2 if center else x0
        for wd in line.split(" "):
            im = Image.new("RGBA", (int(d.textlength(wd, font=f)) + 30, int(f.size * 1.6)), (0, 0, 0, 0))
            items.append([wd, f, (x, y), im]); x += d.textlength(wd + " ", font=f)
        y += lh
    return items, y
def render_words(items, color):
    for it in items: ImageDraw.Draw(it[3]).text((0, 0), it[0], font=it[1], fill=color + (255,))

# ---------- traço à mão ----------
def wobble(pts, amp=1.6, seed=0):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(3)]; out = []; n = len(pts)
    for i, (x, y) in enumerate(pts):
        a = pts[min(i + 1, n - 1)]; b = pts[max(i - 1, 0)]; dx, dy = a[0] - b[0], a[1] - b[1]; L = math.hypot(dx, dy) or 1
        t = i / max(n - 1, 1)
        o = amp * (math.sin(t * 9 + ph[0]) * 0.6 + math.sin(t * 23 + ph[1]) * 0.3 + math.sin(t * 41 + ph[2]) * 0.1)
        out.append((x - dy / L * o, y + dx / L * o))
    return out
def resample(pts, step=3.0):
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); k = max(int(L / step), 1)
        for j in range(1, k + 1): out.append((a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k))
    return out
def catmull(pts, n=20, closed=True):
    out = []; L = len(pts); rng = range(L) if closed else range(L - 1)
    for i in rng:
        p0 = pts[(i - 1) % L] if closed else pts[max(i - 1, 0)]; p1 = pts[i]; p2 = pts[(i + 1) % L]
        p3 = pts[(i + 2) % L] if closed else pts[min(i + 2, L - 1)]
        for k in range(n):
            t = k / n; t2 = t * t; t3 = t2 * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(2)))
    out.append(out[0] if closed else pts[-1]); return out
def circle(cx, cy, r, a0=0, a1=360, n=90):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
def rect(x0, y0, x1, y1): return [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
def star_pts(x, y, r):
    pts = []
    for i in range(8):
        a = math.pi / 4 * i - math.pi / 2; rr = r if i % 2 == 0 else r * 0.3; pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    return pts + [pts[0]]
def blob(cx, cy, r, seed):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    return [(cx + r * (1 + 0.07 * math.sin(3 * t + ph[0]) + 0.05 * math.sin(5 * t + ph[1])) * math.cos(t),
             cy + r * (1 + 0.07 * math.sin(3 * t + ph[0]) + 0.05 * math.sin(5 * t + ph[2])) * math.sin(t)) for t in [i / 120 * 6.283 for i in range(121)]]
def petal(cx, cy, h, w, ang):
    """pétala em forma de gota, base em (cx,cy), apontando no ângulo ang (graus, 0 = para cima)."""
    pts = [(0, 0), (-w * 0.55, -h * 0.38), (-w * 0.30, -h * 0.80), (0, -h), (w * 0.30, -h * 0.80), (w * 0.55, -h * 0.38)]
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    return catmull([(cx + x * c - y * s, cy + x * s + y * c) for x, y in pts], closed=True)

def icon_lotus(th):
    P = [petal(0, 90, 250, 130, 0), petal(-20, 95, 220, 120, -32), petal(20, 95, 220, 120, 32),
         petal(-35, 100, 170, 110, -62), petal(35, 100, 170, 110, 62)]
    water = catmull([(-200, 125), (-100, 112), (0, 128), (100, 112), (200, 125)], closed=False)
    S = [(p, 6) for p in P[::-1]] + [(water, 5), (star_pts(-170, -150, 26), 4), (star_pts(175, -110, 18), 4)]
    return [(blob(0, 10, 235, 1), th["soft"]), (P[0], th["accent"])], S
def icon_sparkle(th):
    S = [(star_pts(-30, 20, 140), 6), (star_pts(120, -110, 60), 5), (star_pts(110, 130, 36), 4), (star_pts(-160, -140, 26), 4)]
    return [(blob(0, 10, 235, 4), th["soft"]), (star_pts(-30, 20, 140), th["accent"])], S
def icon_gift(th):
    box = rect(-140, -20, 140, 170); lid = rect(-165, -80, 165, -20)
    bow_l = catmull([(0, -80), (-60, -150), (-120, -130), (-95, -90)], closed=False)
    bow_r = catmull([(0, -80), (60, -150), (120, -130), (95, -90)], closed=False)
    S = [(box, 6), (lid, 6), ([(0, -80), (0, 170)], 6), (bow_l, 6), (bow_r, 6), (star_pts(185, -150, 26), 4), (star_pts(-190, 60, 18), 4)]
    return [(blob(0, 20, 235, 7), th["soft"]), (box, th["accent"]), ([(-18, -80), (18, -80), (18, 170), (-18, 170)], th["soft"])], S

IS = 640; SC = 2
def draw_icon(spec, th, p, seed):
    fills, strokes = spec
    im = Image.new("RGBA", (IS * SC, IS * SC), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    T = lambda pts: [(IS * SC / 2 + x * SC, IS * SC / 2 + y * SC) for x, y in pts]
    pf = min(max(p / 0.35, 0), 1)
    for i, (pts, col) in enumerate(fills):
        if pf <= 0: break
        k = (0.85 + 0.15 * pf) if i == 0 else 1
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).polygon(T(wobble(resample([(x * k, y * k) for x, y in pts], 4), 1.2, seed + i)), fill=col + (255,))
        if pf < 1: layer.putalpha(layer.getchannel("A").point(lambda v: int(v * pf)))
        im.alpha_composite(layer)
    ps = min(max((p - 0.15) / 0.85, 0), 1)
    if ps > 0:
        total = sum(len(resample(s[0])) for s in strokes); budget = total * ps
        for j, (pts, w) in enumerate(strokes):
            rp = wobble(resample(pts), 1.8, seed * 31 + j)
            if budget <= 1: break
            seg = rp[:int(min(budget, len(rp)))]; budget -= len(rp)
            if len(seg) > 1: d.line(T(seg), fill=th["line"] + (255,), width=w * SC, joint="curve")
            r = w * SC / 2
            for q in (T(seg[:1]) + T(seg[-1:])): d.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=th["line"] + (255,))
    return im.resize((IS, IS), Image.LANCZOS)

# ---------- logo (lótus extraída do logo original + nome em script) ----------
def logo_image(w_target=760):
    src = Image.open(os.path.join(A, "flor_lotus", "logo_original.png")).convert("RGB")
    ic = src.crop((57, 205, 152, 290))
    a = ic.convert("L").point(lambda v: min(255, max(0, (v - 18) * 3)))
    lot = Image.new("RGBA", ic.size, ROSE + (255,)); lot.putalpha(a)
    lot = lot.resize((lot.width * 3, lot.height * 3), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 80, 2))
    f = script(150); d = ImageDraw.Draw(Image.new("RGBA", (1, 1))); tw = int(d.textlength("Flor de Lótus", font=f))
    im = Image.new("RGBA", (lot.width + 30 + tw + 40, max(lot.height, 260)), (0, 0, 0, 0))
    im.alpha_composite(lot, (0, (im.height - lot.height) // 2 - 10))
    d = ImageDraw.Draw(im); d.text((lot.width + 30, im.height // 2 - 20), "Flor de Lótus", font=f, fill=ROSE + (255,), anchor="lm")
    x0, x1 = lot.width + 10, im.width - 10; yb = im.height // 2 + 70
    sw = [(x0 + (x1 - x0) * t, yb + 14 * math.sin(math.pi * t) - 10 * t) for t in [i / 80 for i in range(81)]]
    for k in range(len(sw) - 1):
        wdt = 1 + 3 * math.sin(math.pi * k / 80); d.line([sw[k], sw[k + 1]], fill=ROSE + (255,), width=int(round(wdt)) + 1)
    k = w_target / im.width; return im.resize((w_target, int(im.height * k)), Image.LANCZOS)

# ---------- fotos ----------
def photo_card(code, PW, th, seed, radius=26, label=None):
    ph = Image.open(os.path.join(PD, f"{code}.png")).convert("RGB")
    # quadrado central, levemente aproximado e deslocado p/ cima-esquerda: tira o selo de código do fornecedor (canto inf. dir.)
    s = int(min(ph.size) * 0.80); x0 = int((ph.width - s) * 0.32); y0 = int((ph.height - s) * 0.30)
    ph = ph.crop((x0, y0, x0 + s, y0 + s))
    ph = ph.resize((PW, PW), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 40, 2)).convert("RGBA")
    m = Image.new("L", (PW, PW), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PW - 1), radius=radius, fill=255); ph.putalpha(m)
    off = max(10, PW // 50)
    card = Image.new("RGBA", (PW + off + 8, PW + off + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rounded_rectangle((off + 4, off + 4, PW + off + 4, PW + off + 4), radius=radius, fill=th["accent"] + (255,))
    card.alpha_composite(ph, (4, 4))
    d.line([(4 + x, 4 + y) for x, y in wobble(resample(rect(0, 0, PW, PW)), 1.3, seed)], fill=th["line"] + (255,), width=3, joint="curve")
    return card

def price_pill(price, th):
    f = sans(46, "SemiBold"); d = ImageDraw.Draw(Image.new("RGBA", (1, 1))); t = f"R$ {price}"; tw = d.textlength(t, font=f)
    im = Image.new("RGBA", (int(tw) + 90, 96), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, 95), radius=48, fill=th["accent"] + (255,))
    d.text((im.width / 2, 48), t, font=f, fill=(255, 250, 246, 255), anchor="mm"); return im

# ---------- roteiro ----------
P = lambda code, cat, name, mat, price: dict(prod=True, th=LIGHT, code=code, cat=cat, name=name, mat=mat, price=price)
seq = [
 (3.6, dict(th=DARK, kicker="Novidade na Flor de Lótus", title="Semijoias\nque brilham.", icon=icon_lotus)),
 (3.4, dict(th=LIGHT, title="Pra todo dia\ne toda ocasião.", sub="Anéis, brincos, colares,\npulseiras e relógios.", icon=icon_sparkle)),
 (3.0, P("11896", "Anel", "Anel Tri Zircônia", "Aço inox dourado", "79,90")),
 (3.0, P("11985", "Brinco", "Argola Orgânica", "Aço inox dourado", "79,90")),
 (3.0, P("12106", "Brinco", "Brinco Flor Azul", "Prata banhada", "64,90")),
 (3.0, P("11729", "Conjunto", "Gota Esmeralda", "Colar + brinco · prata banhada", "129,90")),
 (3.0, P("11703", "Choker", "Coração e Pérolas", "Semijoia dourada", "149,90")),
 (3.0, P("11930", "Pulseira", "Zircônia Pink", "Banho italiano", "119,90")),
 (3.0, P("11546", "Relógio", "Relógio Libélula", "Prata com mostrador preto", "279,90")),
 (3.6, dict(th=LIGHT, grid=["12042", "11752", "11672", "11054", "11690", "11810"], title="E muito mais.",
            sub="Mais de 100 peças, a partir de R$ 17,90.")),
 (3.4, dict(th=LIGHT, title="O presente\nperfeito.", sub="Pra você ou pra quem você ama\nneste Natal.", icon=icon_gift)),
 (4.8, dict(th=DARK, end=True)),
]
slides = []; t = 0.0
for d_, s in seq: s["t0"] = t; t += d_; s["t1"] = t; slides.append(s)
DUR = round(t, 2); N = len(slides)
if os.environ.get("DUR_ONLY"): print(DUR); sys.exit(0)

TF = serif(118, 600); SUBF = sans(40); KF = sans(28, "SemiBold")

def build(s, idx):
    th = s["th"]; s["bg"] = background(th); s["hdr"] = header(th); s["seed"] = idx * 10 + 1
    if s.get("end"):
        L = []; lg = logo_image(800); L.append((lg, ((W - lg.width) // 2, 560), 0.0))
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((W / 2, 900), "SEMIJOIAS · ACESSÓRIOS · PRESENTES", font=sans(28, "Medium"), fill=th["gray"] + (255,), anchor="mm")
        L.append((im.crop(im.getbbox()), im.getbbox()[:2], 0.35))
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((W / 2 - 300, 1010, W / 2 + 300, 1116), radius=53, fill=ROSE + (255,))
        d.text((W / 2, 1063), "Peça pelo WhatsApp", font=sans(42, "SemiBold"), fill=NOIR + (255,), anchor="mm")
        d.text((W / 2, 1200), "Pronta entrega", font=serif(56, 500), fill=CREAM + (255,), anchor="mm")
        L.append((im.crop(im.getbbox()), im.getbbox()[:2], 0.65)); s["layers"] = L; return
    if s.get("prod"):
        it, _ = layout_words(s["cat"].upper(), KF, MX, 300, 40); render_words(it, th["accent"]); s["kick"] = it
        s["card"] = photo_card(s["code"], 820, th, s["seed"])
        it, y = layout_words(s["name"], serif(88, 600), MX, 1235, 100); render_words(it, th["ink"]); s["words"] = it
        it2, y = layout_words(s["mat"], sans(34), MX, y + 6, 50); render_words(it2, th["gray"]); s["subw"] = it2
        s["pill"] = price_pill(s["price"], th); s["pill_y"] = y + 34; return
    if s.get("grid"):
        it, y = layout_words(s["title"], TF, MX, 270, 140); render_words(it, th["ink"]); s["words"] = it
        it2, y = layout_words(s["sub"], SUBF, MX, y + 10, 56); render_words(it2, th["gray"]); s["subw"] = it2
        s["cards"] = [photo_card(c, 260, th, s["seed"] + k, radius=18) for k, c in enumerate(s["grid"])]; return
    y = 330
    if s.get("kicker"):
        it, _ = layout_words(s["kicker"].upper(), KF, MX, y, 40); render_words(it, th["accent"]); s["kick"] = it; y += 70
    it, y = layout_words(s["title"], TF, MX, y, 132); render_words(it, th["ink"]); s["words"] = it
    s["title_end"] = 0.15 + len(it) * 0.09 + 0.25
    if s.get("sub"):
        it2, y = layout_words(s["sub"], SUBF, MX, y + 30, 56); render_words(it2, th["gray"]); s["subw"] = it2
    s["spec"] = s["icon"](th); s["icy"] = 1010; s["cache"] = None

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def alpha(im, k):
    if k >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * k))); return im
def words_on(fr, items, lt, start, step):
    for k, (wd, f, (x, y), im) in enumerate(items):
        p = ease((lt - start - k * step) / 0.3)
        if p > 0: fr.alpha_composite(alpha(im, p), (int(x), int(y + (1 - p) * 14)))
def sparkle_at(fr, x, y, r, a, col):
    ov = Image.new("RGBA", (int(r * 2 + 8), int(r * 2 + 8)), (0, 0, 0, 0))
    ImageDraw.Draw(ov).polygon([(p[0] - x + r + 4, p[1] - y + r + 4) for p in star_pts(x, y, r)], fill=col + (int(255 * a),))
    fr.alpha_composite(ov, (int(x - r - 4), int(y - r - 4)))

def render_slide(s, lt):
    fr = s["bg"].copy(); fr.alpha_composite(s["hdr"]); th = s["th"]
    if s.get("end"):
        for im, (x, y), dl in s["layers"]:
            p = ease((lt - dl) / 0.7)
            if p > 0: fr.alpha_composite(alpha(im, p), (int(x), int(y + (1 - p) * 20)))
        for k, (sx, sy, sr) in enumerate(((190, 520, 22), (900, 800, 16), (860, 470, 12), (230, 1180, 14))):
            a = max(0, math.sin(lt * 2.2 + k * 1.7)) * ease((lt - 0.8) / 0.6)
            if a > 0: sparkle_at(fr, sx, sy, sr, a, ROSE)
        return fr
    if s.get("prod"):
        words_on(fr, s["kick"], lt, 0.0, 0.05)
        p = ease((lt - 0.05) / 0.55); card = s["card"]
        z = 1.0 + 0.035 * lt / 3.0                     # zoom lento (ken burns) no cartão
        sc = (0.95 + 0.05 * p) * z; c2 = card.resize((int(card.width * sc), int(card.height * sc)), Image.BICUBIC)
        cx, cy = W // 2, 380 + card.height // 2
        fr.alpha_composite(alpha(c2, p), (int(cx - c2.width / 2), int(cy - c2.height / 2 + (1 - p) * 30)))
        words_on(fr, s["words"], lt, 0.35, 0.08)
        words_on(fr, s["subw"], lt, 0.6, 0.03)
        q = ease((lt - 0.85) / 0.4)
        if q > 0:
            pl = s["pill"]; k = 0.8 + 0.2 * q + 0.04 * math.sin(min(q, 1) * math.pi)
            p2 = pl.resize((int(pl.width * k), int(pl.height * k)), Image.BICUBIC)
            fr.alpha_composite(alpha(p2, q), (int(MX + (pl.width - p2.width) / 2), int(s["pill_y"] + (pl.height - p2.height) / 2)))
        # brilho piscando no canto do cartão
        a = max(0, math.sin((lt - 1.0) * 3.0)) * (1 if lt > 1.0 else 0)
        if a > 0: sparkle_at(fr, W - 130, 380, 26, a, th["accent"])
        return fr
    if s.get("grid"):
        words_on(fr, s["words"], lt, 0.1, 0.09); words_on(fr, s["subw"], lt, 0.5, 0.03)
        gx0 = (W - 3 * 290 + 30) // 2
        for k, card in enumerate(s["cards"]):
            p = ease((lt - 0.4 - k * 0.12) / 0.45)
            if p > 0:
                x = gx0 + (k % 3) * 290; y = 760 + (k // 3) * 320
                fr.alpha_composite(alpha(card, p), (x, int(y + (1 - p) * 30)))
        return fr
    if s.get("kick"): words_on(fr, s["kick"], lt, 0.0, 0.05)
    words_on(fr, s["words"], lt, 0.15, 0.09)
    if s.get("subw"): words_on(fr, s["subw"], lt, s["title_end"], 0.04)
    p = min(max((lt - 0.25) / 1.1, 0), 1)
    if p >= 1:
        if s["cache"] is None: s["cache"] = draw_icon(s["spec"], th, 1, s["seed"])
        ic = s["cache"]
    else: ic = draw_icon(s["spec"], th, ease(p) if p > 0 else 0, s["seed"])
    fr.alpha_composite(ic, ((W - IS) // 2, int(s["icy"] + math.sin(lt * 1.4) * 5)))
    return fr

def bars(fr, t, th):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); gap = 12; segw = (W - 2 * MX - gap * (N - 1)) / N; y = 1790
    for i, s in enumerate(slides):
        x = MX + i * (segw + gap); d.rounded_rectangle((x, y, x + segw, y + 6), radius=3, fill=th["base"] + (255,))
        p = min(max((t - s["t0"]) / (s["t1"] - s["t0"]), 0), 1)
        if p > 0: d.rounded_rectangle((x, y, x + max(segw * p, 6), y + 6), radius=3, fill=th["accent"] + (255,))
    fr.alpha_composite(ov)

for i, s in enumerate(slides): build(s, i)
XF = 0.35; out = sys.stdout.buffer
prev = [float(x) for x in os.environ.get("PREV_TS", "2.5,5.5,8.5,17.5,30,33.5,37.5").split(",")] if PREVIEW else None
for n in range(int(round(DUR * FPS))):
    t = n / FPS
    if PREVIEW and not any(abs(t - pt) < 0.5 / FPS for pt in prev): continue
    i = max(k for k, s in enumerate(slides) if s["t0"] <= t); s = slides[i]
    fr = render_slide(s, t - s["t0"])
    if i > 0 and t - s["t0"] < XF:
        ps = slides[i - 1]; fr = Image.blend(render_slide(ps, t - ps["t0"]), fr, ease((t - s["t0"]) / XF))
    bars(fr, t, s["th"] if not (i > 0 and t - s["t0"] < XF / 2) else slides[i - 1]["th"])
    if n < 8: fr = Image.blend(Image.new("RGBA", (W, H), NOIR + (255,)), fr, n / 8)
    if PREVIEW: fr.convert("RGB").save(f"{PREVIEW}/f{t:05.2f}.png")
    else: out.write(fr.convert("RGB").tobytes())
