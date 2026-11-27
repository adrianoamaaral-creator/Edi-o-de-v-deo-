"""Versão curta em estética editorial "estilo Claude": marfim, serifa, traço à mão, terracota.
Uso: claude_style.py FONTS_DIR - [PREVIEW_DIR]   (sem preview: escreve frames RGB24 1080x1920@30 em stdout)
Env: LOGO=assets/logo_bblips_mask.png  PREV_TS=1.5,4,...  (tempos para preview)
Sincronizado com tools/cut_audio.py (25 s)."""
import sys, os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FD = sys.argv[1]; PREVIEW = sys.argv[3] if len(sys.argv) > 3 else None
W, H, FPS, DUR = 1080, 1920, 30, 25.0

# ---------- paleta ----------
IVORY = (244, 241, 234); IVORY2 = (238, 233, 222)
INK = (20, 20, 19); GRAY = (115, 114, 108); CLAY = (217, 119, 87); CLAY_SOFT = (235, 200, 180)
DARKBG = (38, 38, 36); DARKBG2 = (30, 30, 28); IVORY_TXT = (240, 236, 226)
LIGHT = dict(bg=(IVORY, IVORY2), ink=INK, gray=GRAY, accent=CLAY, base=(214, 209, 198), line=INK)
DARK = dict(bg=(DARKBG, DARKBG2), ink=IVORY_TXT, gray=(170, 166, 156), accent=CLAY, base=(70, 69, 65), line=IVORY_TXT)

def serif(s, w=400, italic=False):
    f = ImageFont.truetype(FD + ("/SourceSerif4-Italic.ttf" if italic else "/SourceSerif4.ttf"), s)
    f.set_variation_by_axes([w, 60 if s > 40 else 20]); return f
def sans(s, w=400):
    f = ImageFont.truetype(FD + "/Inter.ttf", s); f.set_variation_by_axes([32 if s > 30 else 14, w]); return f

MX = 110
def background(th):
    c1, c2 = th["bg"]; g = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / (H - 1); g.putpixel((0, y), tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3)))
    im = g.resize((W, H))
    rnd = random.Random(7); noise = Image.effect_noise((W // 2, H // 2), 40).resize((W, H)).filter(ImageFilter.GaussianBlur(0.6))
    grain = Image.merge("RGB", [noise] * 3)
    im = Image.blend(im, grain, 0.035)
    return im.convert("RGBA")

def header(th):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((MX, 150), "BBLips", font=serif(34, 500), fill=th["ink"] + (255,))
    f = sans(22, 500); t = "Estética avanzada · Bruna Borges"
    d.text((W - MX - d.textlength(t, font=f), 160), t, font=f, fill=th["gray"] + (255,))
    return im

# ---------- texto palavra por palavra ----------
def layout_words(text, f, x0, y0, lh):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1))); items = []; y = y0
    for line in text.split("\n"):
        x = x0
        for wd in line.split(" "):
            im = Image.new("RGBA", (int(d.textlength(wd, font=f)) + 20, int(f.size * 1.5)), (0, 0, 0, 0))
            items.append([wd, f, (x, y), im]); x += d.textlength(wd + " ", font=f)
        y += lh
    return items, y
def render_words(items, color):
    for it in items:
        wd, f, _, im = it; ImageDraw.Draw(im).text((0, 0), wd, font=f, fill=color + (255,))
        it[3] = im.crop(im.getbbox() and (0, 0, im.width, im.height))

# ---------- traço à mão ----------
def wobble(pts, amp=1.6, seed=0):
    rnd = random.Random(seed); ph = [rnd.uniform(0, 6.28) for _ in range(3)]; out = []
    n = len(pts)
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
    if closed: out.append(out[0])
    else: out.append(pts[-1])
    return out
def circle(cx, cy, r, a0=0, a1=360, n=90):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
def rot(pts, a, ox=0, oy=0):
    c, s = math.cos(a), math.sin(a); return [(ox + x * c - y * s, oy + x * s + y * c) for x, y in pts]
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
def lips_strokes(cx=0, cy=0, s=1.0):
    a = 150 * s; h = 72 * s
    upper = [(-a, 0), (-a * 0.6, -h * 0.45), (-a * 0.28, -h * 0.8), (0, -h * 0.5), (a * 0.28, -h * 0.8), (a * 0.6, -h * 0.45), (a, 0)]
    lower = [(a, 0), (a * 0.6, h * 0.55), (0, h * 0.85), (-a * 0.6, h * 0.55), (-a, 0)]
    mid = [(-a * 0.95, 0), (-a * 0.5, h * 0.1), (0, h * 0.16), (a * 0.5, h * 0.1), (a * 0.95, 0)]
    f = lambda p: [(cx + x, cy + y) for x, y in catmull(p, closed=False)]
    return [f(upper), f(lower), f(mid)], [(cx + x, cy + y) for x, y in catmull(upper[:-1] + [(a, 0)] + lower[1:-1], closed=True)]

# Cada ícone: (fills, strokes). fills = [(pts, color)], strokes = [(pts, width)]
def icon_syringe():
    a = math.radians(-38); S = []
    S.append((rot(rect(-110, -30, 70, 30), a), 6)); S.append((rot([(70, 0), (175, 0)], a), 4))
    S.append((rot([(-110, 0), (-175, 0)], a), 6)); S.append((rot([(-175, -34), (-175, 34)], a), 6)); S.append((rot([(-110, -52), (-110, 52)], a), 6))
    for x in (-40, 0, 40): S.append((rot([(x, -30), (x, -10)], a), 3))
    S.append((circle(0, 0, 205), 7)); S.append((rot([(-205, 0), (205, 0)], math.radians(45)), 7))
    return [(blob(10, 10, 230, 1), CLAY_SOFT), (rot(rect(-60, -30, 70, 30), a), CLAY)], S
def icon_volume():
    st, fill = lips_strokes(0, 70, 1.05); S = [(p, 6) for p in st]
    for x in (-95, 0, 95):
        S.append(([(x, -10), (x, -150)], 5)); S.append(([(x - 22, -122), (x, -152), (x + 22, -122)], 5))
    return [(blob(0, 20, 235, 2), CLAY_SOFT), (fill, CLAY)], S
def icon_pen():
    a = math.radians(-35); S = []
    S.append((rot([(-200, -36), (110, -36), (160, -22), (200, -8), (200, 8), (160, 22), (110, 36), (-200, 36), (-200, -36)], a), 6))
    S.append((rot([(-130, -36), (-130, 36)], a), 5)); S.append((rot([(110, -36), (110, 36)], a), 5)); S.append((rot([(160, -22), (160, 22)], a), 4))
    S.append((star_pts(-170, -170, 30), 4)); S.append((star_pts(185, 160, 20), 4))
    return [(blob(0, 0, 235, 3), (70, 52, 46)), (rot([(-200, -36), (-130, -36), (-130, 36), (-200, 36)], a), CLAY)], S
def icon_sparkle():
    S = [(star_pts(-30, 20, 140), 6), (star_pts(120, -110, 60), 5), (star_pts(110, 130, 36), 4), (star_pts(-160, -140, 26), 4)]
    return [(blob(0, 10, 235, 4), CLAY_SOFT), (star_pts(-30, 20, 140), CLAY)], S
def icon_heart():
    pts = [(16 * math.sin(t) ** 3 * 11, -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * 11 - 10) for t in [i / 160 * 6.283 for i in range(161)]]
    st, fill = lips_strokes(0, -5, 0.55)
    S = [(pts, 6)] + [(p, 5) for p in st] + [(star_pts(195, -170, 24), 4)]
    return [(blob(0, 0, 235, 5), CLAY_SOFT), (pts, CLAY), (fill, IVORY)], S
def icon_final():
    st, fill = lips_strokes(0, 20, 1.1)
    S = [(p, 6) for p in st] + [(star_pts(-180, -130, 32), 4), (star_pts(190, -100, 22), 4), (star_pts(160, 170, 26), 4)]
    return [(blob(0, 10, 235, 6), CLAY_SOFT), (fill, CLAY)], S

IS = 640; SC = 2
def draw_icon(spec, th, p, seed):
    """p em [0,1]: manchas surgem, depois o traço se desenha."""
    fills, strokes = spec
    im = Image.new("RGBA", (IS * SC, IS * SC), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    T = lambda pts: [(IS * SC / 2 + x * SC, IS * SC / 2 + y * SC) for x, y in pts]
    pf = min(max(p / 0.35, 0), 1)
    for i, (pts, col) in enumerate(fills):
        if pf <= 0: break
        k = (0.85 + 0.15 * pf) if i == 0 else 1
        pts2 = [(x * k, y * k) for x, y in pts]
        a = int(255 * pf)
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(layer).polygon(T(wobble(resample(pts2, 4), 1.2, seed + i)), fill=col + (255,))
        if a < 255: layer.putalpha(layer.getchannel("A").point(lambda v: v * a // 255))
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

# ---------- slides (tempos sincronizados com cut_audio.py) ----------
slides = [
 dict(t0=0.0, t1=2.87, th=LIGHT, title="¿Miedo a\nlas agujas?", icon=icon_syringe),
 dict(t0=2.87, t1=5.9, th=LIGHT, title="¿Quieres más\nvolumen?", sub="Labios más llenos y definidos.", icon=icon_volume),
 dict(t0=5.9, t1=10.4, th=DARK, kicker="Te presento", title="Hyaluron Pen", sub="Volumen en labios, sin agujas.", icon=icon_pen),
 # antes/después de labios (fotos em assets/labios)
 dict(t0=10.4, t1=16.3, th=LIGHT, ba=True, imgs=("labios2/antes_recorte.png", "labios2/despues_recorte.png"), pw_w=580, ph_h=446, lips_ring=3.3,
      d_start=1.6, circle=False, note="Resultados reales · Los resultados pueden variar.",
      phases=[(0.0, "Más natural.", "Un volumen sutil y armonioso."), (3.2, "El resultado.", "Te va a encantar.")]),
 dict(t0=16.3, t1=21.4, th=LIGHT, title="Ya no hay\nexcusa.", sub="Para lucir tus labios con volumen.", icon=icon_final),
 dict(t0=21.4, t1=DUR, th=LIGHT, end=True),
]

def icon_dual():
    st, fill = lips_strokes(-95, 30, 0.55)
    S = [(p, 5) for p in st]
    # silhueta simples de corpo (cintura) à direita
    body_l = [(70, -150), (60, -90), (80, -20), (62, 60), (75, 150)]
    body_r = [(170, -150), (180, -90), (160, -20), (178, 60), (165, 150)]
    S += [(catmull(body_l, closed=False), 5), (catmull(body_r, closed=False), 5)]
    S += [(star_pts(-150, -120, 26), 4), (star_pts(215, -60, 18), 4)]
    return [(blob(-95, 20, 140, 11), CLAY_SOFT), (blob(120, 10, 125, 12), CLAY_SOFT), (fill, CLAY)], S


# ---------- ícones extras (micropigmentação) ----------
def icon_lips_dots():
    st, fill = lips_strokes(0, 20, 1.15)
    S = [(p, 6) for p in st]
    # contorno pontilhado (marcação do desenho)
    a = 150 * 1.15 * 1.12; h = 72 * 1.15 * 1.18
    for k in range(34):
        t = k / 34 * 2 * math.pi; x = a * math.cos(t); y = 20 + h * math.sin(t) * (0.95 if math.sin(t) > 0 else 1.05)
        S.append((circle(x, y, 3.5, n=10), 3))
    # gota de pigmento
    drop = [(185, -175), (205, -140), (208, -122), (198, -105), (185, -100), (172, -105), (162, -122), (165, -140), (185, -175)]
    S.append((catmull(drop[:-1], closed=True), 5))
    return [(blob(0, 15, 235, 21), CLAY_SOFT), (fill, CLAY), (catmull(drop[:-1], closed=True), CLAY)], S
def icon_sun_drop():
    S = [(circle(-60, -40, 75), 6)]
    for k in range(10):
        ang = k / 10 * 2 * math.pi; S.append(([(-60 + 100 * math.cos(ang), -40 + 100 * math.sin(ang)), (-60 + 135 * math.cos(ang), -40 + 135 * math.sin(ang))], 5))
    S.append((circle(-60, -40, 205, n=120)[10:50], 0))  # (guia invisível)
    S = [x for x in S if x[1] > 0]
    S.append(([(-205, -185), (85, 105)], 7))  # risco "evitar o sol"
    drop = [(150, 40), (185, 105), (190, 135), (175, 165), (150, 175), (125, 165), (110, 135), (115, 105)]
    S.append((catmull(drop, closed=True), 6))
    return [(blob(0, 0, 235, 22), CLAY_SOFT), (circle(-60, -40, 75), (245, 214, 170)), (catmull(drop, closed=True), CLAY)], S
def icon_hourglass():
    S = [([(-130, -190), (130, -190)], 7), ([(-130, 190), (130, 190)], 7),
         (catmull([(-105, -190), (-95, -90), (-20, -10), (-95, 90), (-105, 190)], closed=False), 6),
         (catmull([(105, -190), (95, -90), (20, -10), (95, 90), (105, 190)], closed=False), 6),
         (star_pts(185, -150, 24), 4)]
    sand_top = [(-80, -110), (80, -110), (15, -25), (-15, -25)]
    sand_bot = [(-90, 185), (90, 185), (50, 120), (0, 95), (-50, 120)]
    return [(blob(0, 0, 235, 23), CLAY_SOFT), (sand_top, CLAY), (sand_bot, CLAY)], S

if os.environ.get("STORY") == "micro":
    DUR = 32.0
    slides = [
     dict(t0=0.0, t1=3.8, th=DARK, kicker="Nuevo en BBLips", title="Micropigmentación\nlabial", tsize=86, icon=icon_final),
     dict(t0=3.8, t1=8.6, th=LIGHT, title="¿Qué es?", sub="Pigmento en la capa más superficial\nde la piel para dar color, definición\ny vida a tus labios.", icon=icon_lips_dots),
     dict(t0=8.6, t1=13.8, th=LIGHT, title="Beneficios", sub="•  Color uniforme y natural\n•  Contorno más definido\n•  Efecto más jugoso\n•  Te levantas lista", icon=icon_sparkle),
     dict(t0=13.8, t1=19.0, th=LIGHT, title="El proceso", sub="1.  Diseño y color a tu medida\n2.  Anestesia tópica\n3.  Pigmentación, con calma y precisión", icon=icon_heart),
     dict(t0=19.0, t1=24.2, th=LIGHT, title="Cuidados", sub="Los primeros días el color es más\nintenso. Hidrata los labios y\nevita el sol.", icon=icon_sun_drop),
     dict(t0=24.2, t1=28.4, th=DARK, kicker="Duración", title="De 1 a 3 años", sub="Con un retoque a las 4–6 semanas.", icon=icon_hourglass),
     dict(t0=28.4, t1=DUR, th=LIGHT, end=True),
    ]
if os.environ.get("STORY") == "v4":
    # Versão com a narração gravada (47,3 s) — tempos seguem a fala
    DUR = 47.3
    slides = [
     dict(t0=0.0, t1=2.2, th=LIGHT, title="¿Miedo a\nlas agujas?", icon=icon_syringe),
     dict(t0=2.2, t1=5.5, th=DARK, kicker="Te presento", title="Hyaluron Pen", sub="Volumen sin agujas.", icon=icon_pen,
          photo="bruna/bruna_hyaluron_pen.jpg", photo_box=(60, 430, 1071, 1720), photo_w=620),
     dict(t0=5.5, t1=16.0, th=LIGHT, title="Una clienta\nde años.", sub="Comenzó conmigo hace unos años.", icon=icon_heart),
     dict(t0=16.0, t1=37.0, th=LIGHT, ba=True, imgs=("labios2/antes_recorte.png", "labios2/despues_recorte.png"),
          pw_w=580, ph_h=446, py0=640, d_start=1.6, circle=False, lips_ring=4.2, lips_ring_end=9.3, fold_rings=11.9,
          note="Resultados reales · Los resultados pueden variar.",
          phases=[(0.0, "Más volumen.", "Sutil y mucho más natural."), (9.7, "Y el surco\nnasogeniano.", None),
                  (15.7, "De la nariz a la\ncomisura.", None)]),
     dict(t0=37.0, t1=40.9, th=LIGHT, title="Sin agujas.", sub="Todo este resultado, sin agujas.", icon=icon_syringe),
     dict(t0=40.9, t1=DUR, th=LIGHT, end=True),
    ]
if os.environ.get("STORY") == "v4" and os.environ.get("TIMEMAP"):
    # narração com pausas encurtadas: converte os tempos originais para a nova linha do tempo
    import json
    _MAP = json.load(open(os.environ["TIMEMAP"]))
    def remap(t):
        prev_end = 0.0
        for k0, k1, nt in _MAP:
            if t < k0: return prev_end if prev_end else max(nt - (k0 - t), 0.0)
            if t <= k1: return nt + (t - k0)
            prev_end = nt + (k1 - k0)
        return prev_end + (t - _MAP[-1][1])
    _speech_end = remap(46.7)
    for sl in slides:
        if sl.get("ba"):
            b0 = sl["t0"]; nb0 = remap(b0)
            for key in ("d_start", "lips_ring", "lips_ring_end", "fold_rings"):
                if sl.get(key) is not None: sl[key] = remap(b0 + sl[key]) - nb0
            sl["phases"] = [(remap(b0 + t) - nb0 if t else 0.0, ti, su) for t, ti, su in sl["phases"]]
        sl["t0"] = remap(sl["t0"]) if sl["t0"] else 0.0
    for a_, b_ in zip(slides, slides[1:]): a_["t1"] = b_["t0"]
    DUR = round(max(_speech_end + 2.0, slides[-1]["t0"] + 5.0), 2); slides[-1]["t1"] = DUR
if os.environ.get("STORY") == "v3":
    # Versão SEM VOZ para regravar o áudio: lábios + surco nasogeniano da mesma cliente (24 s)
    DUR = 24.0
    slides = [
     dict(t0=0.0, t1=4.0, th=DARK, kicker="Sin agujas", title="Hyaluron Pen", icon=icon_pen),
     dict(t0=4.0, t1=16.0, th=LIGHT, ba=True, imgs=("labios2/antes_recorte.png", "labios2/despues_recorte.png"),
          pw_w=580, ph_h=446, d_start=1.4, circle=False, lips_ring=2.8, lips_ring_end=6.7, fold_rings=7.3,
          note="Resultados reales · Los resultados pueden variar.",
          phases=[(0.0, "Más volumen.", "Labios sutiles y naturales."), (7.0, "Y el surco\nnasogeniano.", None)]),
     dict(t0=16.0, t1=19.5, th=LIGHT, title="Sin agujas.", sub="Volumen y armonía, sin pinchazos.", icon=icon_syringe),
     dict(t0=19.5, t1=DUR, th=LIGHT, end=True),
    ]
if os.environ.get("STORY") == "v2":
    DUR = 24.0
    slides = [
     dict(t0=0.0, t1=4.6, th=DARK, kicker="Para quien no lo conoce", title="Hyaluron Pen", icon=icon_pen),
     dict(t0=4.6, t1=8.5, th=LIGHT, title="Facial y\ncorporal.", sub="Sirve para tratamientos de cuerpo y rostro.", icon=icon_dual),
     dict(t0=8.5, t1=17.6, th=LIGHT, ba=True, phases=[(0.0, "De esto…", None), (2.8, "…a esto.", None),
          (4.5, "Adiós a las marcas.", "Del surco nasogeniano, sin agujas.")]),
     dict(t0=17.6, t1=20.6, th=LIGHT, title="Sin agujas.", sub="Y sin sufrimiento.", icon=icon_syringe),
     dict(t0=20.6, t1=DUR, th=LIGHT, end=True),
    ]
N = len(slides)
TF = serif(104, 450); SUBF = sans(40, 400); KF = sans(28, 600)

def build(s, idx):
    th = s["th"]; s["bg"] = background(th); s["hdr"] = header(th); s["seed"] = idx * 10 + 1
    if s.get("end"):
        L = []
        m = Image.open(os.environ["LOGO"]).getchannel("A"); lw = 520; m = m.resize((lw, int(m.height * lw / m.width)), Image.LANCZOS)
        logo = Image.new("RGBA", m.size, INK + (255,)); logo.putalpha(m); L.append((logo, ((W - lw) // 2, 330), 0.0))
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((W / 2, 930), "Bruna Borges", font=serif(66, 450, True), fill=INK + (255,), anchor="mm")
        d.text((W / 2, 1000), "Estética avanzada · Especialista en labios", font=sans(32, 400), fill=GRAY + (255,), anchor="mm")
        L.append((im.crop(im.getbbox()), im.getbbox()[:2], 0.3))
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((W / 2 - 240, 1110, W / 2 + 240, 1206), radius=22, fill=CLAY + (255,))
        d.text((W / 2, 1158), "Reserva tu cita", font=sans(40, 600), fill=(250, 247, 240, 255), anchor="mm")
        d.text((W / 2, 1290), "@brunaborgesestetic", font=sans(34, 500), fill=GRAY + (255,), anchor="mm")
        L.append((im.crop(im.getbbox()), im.getbbox()[:2], 0.55)); s["layers"] = L; return
    if s.get("ba"):
        ph = []
        for (t, title, sub) in s["phases"]:
            it, y2 = layout_words(title, TF, MX, 330, 124); render_words(it, th["ink"]); sw = None
            if sub: sw, _ = layout_words(sub, SUBF, MX, y2 + 30, 56); render_words(sw, th["gray"])
            ph.append((t, it, sw))
        s["ph"] = ph
        ad = os.path.dirname(os.environ["LOGO"])
        imgs = s.get("imgs", ("antes_despues/antes.png", "antes_despues/despues.png"))
        PW, PH = s.get("pw_w", 520), s.get("ph_h", 388); s["pw"] = (PW, PH)
        def framed(path, label):
            ph_ = Image.open(path).convert("RGBA").resize((PW, PH), Image.LANCZOS)
            m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), radius=18, fill=255); ph_.putalpha(m)
            card = Image.new("RGBA", (PW + 20, PH + 80), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
            d.text((4, 0), label, font=sans(30, 600), fill=th["ink"] + (255,))
            d.rounded_rectangle((14, 64, PW + 14, PH + 60), radius=18, fill=CLAY_SOFT + (255,))
            card.alpha_composite(ph_, (4, 54))
            T = [(4 + x, 54 + y) for x, y in wobble(resample(rect(0, 0, PW, PH)), 1.2, 5)]
            d.line(T, fill=th["ink"] + (255,), width=3, joint="curve")
            return card
        s["antes"] = framed(os.path.join(ad, imgs[0]), "Antes"); s["despues"] = framed(os.path.join(ad, imgs[1]), "Después")
        s["py"] = s.get("py0", 600)
        im = Image.new("RGBA", (W, 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((W / 2, 10), s.get("note", "Imágenes del vídeo original · Los resultados pueden variar."), anchor="ma", font=sans(24, 400), fill=th["gray"] + (255,))
        s["note"] = im; return
    y = 330
    if s.get("kicker"):
        it, _ = layout_words(s["kicker"].upper(), KF, MX, y, 40); render_words(it, th["accent"]); s["kick"] = it; y += 70
    tf = serif(s["tsize"], 450) if s.get("tsize") else TF
    it, y = layout_words(s["title"], tf, MX, y, int(tf.size * 1.19)); render_words(it, th["ink"]); s["words"] = it
    s["title_end"] = 0.15 + len(it) * 0.09 + 0.25
    if s.get("sub"):
        it2, y = layout_words(s["sub"], SUBF, MX, y + 30, 56); render_words(it2, th["gray"]); s["subw"] = it2
    if s.get("photo"):   # foto em moldura à mão no lugar da ilustração
        ph_ = Image.open(os.path.join(os.path.dirname(os.environ["LOGO"]), s["photo"])).convert("RGBA")
        bx = s.get("photo_box"); ph_ = ph_.crop(bx) if bx else ph_
        PW = s.get("photo_w", 600); PH = int(ph_.height * PW / ph_.width); ph_ = ph_.resize((PW, PH), Image.LANCZOS)
        m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), radius=22, fill=255); ph_.putalpha(m)
        card = Image.new("RGBA", (PW + 24, PH + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rounded_rectangle((16, 16, PW + 16, PH + 16), radius=22, fill=th["accent"] + (255,))
        card.alpha_composite(ph_, (4, 4))
        d.line([(4 + x, 4 + y) for x, y in wobble(resample(rect(0, 0, PW, PH)), 1.4, 9)], fill=th["line"] + (255,), width=3, joint="curve")
        s["photo_img"] = card; s["photo_y"] = s.get("photo_y", y + 50); return
    s["spec"] = s["icon"](); s["icy"] = 1000; s["cache"] = None

def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def alpha(im, k):
    if k >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * k))); return im

def words_on(fr, items, lt, start, step):
    for k, (wd, f, (x, y), im) in enumerate(items):
        p = ease((lt - start - k * step) / 0.3)
        if p > 0: fr.alpha_composite(alpha(im, p), (int(x), int(y + (1 - p) * 14)))

def render_slide(s, lt):
    fr = s["bg"].copy(); fr.alpha_composite(s["hdr"]); th = s["th"]
    if s.get("end"):
        for im, (x, y), dl in s["layers"]:
            p = ease((lt - dl) / 0.6)
            if p > 0: fr.alpha_composite(alpha(im, p), (int(x), int(y + (1 - p) * 20)))
        return fr
    if s.get("ba"):
        ph = s["ph"]
        for j, (t, it, sw) in enumerate(ph):
            nxt = ph[j + 1][0] if j + 1 < len(ph) else 1e9
            if lt < t or lt > nxt + 0.25: continue
            tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            words_on(tmp, it, lt, t + 0.05, 0.08)
            if sw: words_on(tmp, sw, lt, t + 0.05 + len(it) * 0.08 + 0.2, 0.04)
            k = 1 - min(max((lt - nxt) / 0.25, 0), 1)
            fr.alpha_composite(alpha(tmp, k))
        PW, PH = s["pw"]; y0 = s["py"]
        CX = (W - PW) // 2 - 4; Y2 = y0 + PH + 90
        for card, yy, st in ((s["antes"], y0, 0.15), (s["despues"], Y2, s.get("d_start", 2.8))):
            p = ease((lt - st) / 0.5)
            if p > 0: fr.alpha_composite(alpha(card, p), (CX, int(yy + (1 - p) * 30)))
        # círculo à mão sobre o sulco nasogeniano (desenha a partir da fase 3)
        p = min(max((lt - 4.7) / 0.9, 0), 1)
        if p > 0 and s.get("circle", True):
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
            for k, yy in enumerate((y0, Y2)):
                pts = [(CX + 4 + 142 + 77 * math.cos(a), yy + 54 + 204 + 118 * math.sin(a)) for a in [-1.9 + 6.6 * i / 120 for i in range(121)]]
                pts = wobble(pts, 2.0, 40 + k)[:max(2, int(121 * ease(p)))]
                d.line(pts, fill=CLAY + (255,), width=7, joint="curve")
            fr.alpha_composite(ov)
        if s.get("lips_ring") is not None:   # contorno à mão em volta dos lábios no "Después"
            p = min(max((lt - s["lips_ring"]) / 0.9, 0), 1)
            fade = 1.0
            if s.get("lips_ring_end") is not None: fade = 1 - min(max((lt - s["lips_ring_end"]) / 0.4, 0), 1)
            if p > 0 and fade > 0:
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
                ecx, ecy = CX + 4 + PW / 2, Y2 + 54 + PH * 0.47
                pts = [(ecx + PW * 0.34 * math.cos(a), ecy + PH * 0.25 * math.sin(a)) for a in [3.6 + 6.7 * i / 140 for i in range(141)]]
                pts = wobble(pts, 2.2, 77)[:max(2, int(141 * ease(p)))]
                d.line(pts, fill=CLAY + (255,), width=8, joint="curve"); fr.alpha_composite(alpha(ov, fade))
        if s.get("fold_rings") is not None:   # marcas do surco nasogeniano (dos dois lados da boca), nas duas fotos
            p = min(max((lt - s["fold_rings"]) / 1.0, 0), 1)
            if p > 0:
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
                for k, yy in enumerate((y0, Y2)):
                    for j, fx in enumerate((0.27, 0.73)):
                        ecx, ecy = CX + 4 + PW * fx, yy + 54 + PH * 0.36
                        pts = [(ecx + PW * 0.075 * math.cos(a), ecy + PH * 0.22 * math.sin(a)) for a in [-1.7 + 6.7 * i / 100 for i in range(101)]]
                        pts = wobble(pts, 1.6, 90 + k * 2 + j)[:max(2, int(101 * ease(p)))]
                        d.line(pts, fill=CLAY + (255,), width=6, joint="curve")
                fr.alpha_composite(ov)
        if lt > 0.6: fr.alpha_composite(alpha(s["note"], ease((lt - 0.6) / 0.5)), (0, Y2 + PH + 76))
        return fr
    if s.get("kick"): words_on(fr, s["kick"], lt, 0.0, 0.05)
    words_on(fr, s["words"], lt, 0.15, 0.09)
    # "cursor" terracota pulsando enquanto o título é escrito
    if lt < s["title_end"] + 0.5:
        k = min((lt - 0.15) / 0.09, len(s["words"]) - 1)
        if k >= 0:
            wd, f, (x, y), im = s["words"][int(max(k, 0))]
            cx = x + im.getbbox()[2] + 26 if im.getbbox() else x; cy = y + 70
            a = 0.5 + 0.5 * math.sin(lt * 10)
            if lt > s["title_end"]: a *= max(0, 1 - (lt - s["title_end"]) / 0.5)
            ImageDraw.Draw(fr).ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=th["accent"] + (int(255 * a),)) if False else None
            dot = Image.new("RGBA", (30, 30), (0, 0, 0, 0)); ImageDraw.Draw(dot).ellipse((2, 2, 28, 28), fill=th["accent"] + (int(255 * a),))
            fr.alpha_composite(dot, (int(cx - 15), int(cy - 15)))
    if s.get("subw"): words_on(fr, s["subw"], lt, s["title_end"], 0.04)
    if s.get("photo_img") is not None:
        p = ease((lt - 0.2) / 0.6); card = s["photo_img"]
        if p > 0:
            sc = 0.94 + 0.06 * p; c2 = card.resize((int(card.width * sc), int(card.height * sc)), Image.BICUBIC) if sc < 0.999 else card
            fr.alpha_composite(alpha(c2, p), ((W - c2.width) // 2, int(s["photo_y"] + (card.height - c2.height) / 2 + (1 - p) * 30)))
        return fr
    p = min(max((lt - 0.25) / 1.1, 0), 1)
    if p >= 1:
        if s["cache"] is None: s["cache"] = draw_icon(s["spec"], th, 1, s["seed"])
        ic = s["cache"]
    else: ic = draw_icon(s["spec"], th, ease(p) if p > 0 else 0, s["seed"])
    fl = math.sin(lt * 1.4) * 5
    fr.alpha_composite(ic, ((W - IS) // 2, int(s["icy"] + fl)))
    return fr

def bars(fr, t, th):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov); gap = 14; segw = (W - 2 * MX - gap * (N - 1)) / N; y = 1760
    for i, s in enumerate(slides):
        x = MX + i * (segw + gap); d.rounded_rectangle((x, y, x + segw, y + 6), radius=3, fill=th["base"] + (255,))
        p = min(max((t - s["t0"]) / (s["t1"] - s["t0"]), 0), 1)
        if p > 0: d.rounded_rectangle((x, y, x + max(segw * p, 6), y + 6), radius=3, fill=th["accent"] + (255,))
    fr.alpha_composite(ov)

if os.environ.get("DUR_ONLY"): print(DUR); sys.exit(0)
for i, s in enumerate(slides): build(s, i)
XF = 0.35; out = sys.stdout.buffer
prev = [float(x) for x in os.environ.get("PREV_TS", "1.5,4.5,8,12,15,19,23.5").split(",")] if PREVIEW else None
for n in range(int(round(DUR * FPS))):
    t = n / FPS
    if PREVIEW and not any(abs(t - pt) < 0.5 / FPS for pt in prev): continue
    i = max(k for k, s in enumerate(slides) if s["t0"] <= t); s = slides[i]
    fr = render_slide(s, t - s["t0"])
    if i > 0 and t - s["t0"] < XF:
        ps = slides[i - 1]; fr = Image.blend(render_slide(ps, t - ps["t0"]), fr, ease((t - s["t0"]) / XF))
    bars(fr, t, s["th"] if not (i > 0 and t - s["t0"] < XF / 2) else slides[i - 1]["th"])
    if n < 8: fr = Image.blend(Image.new("RGBA", (W, H), IVORY + (255,)), fr, n / 8)
    if PREVIEW: fr.convert("RGB").save(f"{PREVIEW}/c{t:05.2f}.png")
    else: out.write(fr.convert("RGB").tobytes())
