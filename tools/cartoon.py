"""Curta animado com bonecos (estilo cartoon vetorial) — história da Lucía e o Hyaluron Pen.
Uso: python3 tools/cartoon.py video | ffmpeg -f rawvideo -pix_fmt bgra -s 1080x1920 -r 30 -i - ...
     python3 tools/cartoon.py audio saida.wav        (trilha + efeitos sincronizados)
     python3 tools/cartoon.py preview DIR 1.0 5.2 ...
Requer: pip install pycairo numpy pillow"""
import sys, math, random, os, wave
import cairo, numpy as np
from PIL import Image

W, H, FPS, DUR = 1080, 1920, 30, 24.5
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "assets", "logo_bblips_mask.png")
LOGO_SURF = cairo.ImageSurface.create_from_png(LOGO) if os.path.exists(LOGO) else None

def rgb(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
OL = rgb("2b1f2b")                     # contorno
SKIN, SKIN2 = rgb("f6c9a8"), rgb("c98b62")
WHITE = (1, 1, 1); YELLOW = rgb("ffd23f"); ROSE = rgb("c0566e"); ROSE_D = rgb("8c4a5e"); PINK = rgb("f4a7b9")

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a))
def out_cubic(x): return 1 - (1 - x) ** 3
def in_out(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def out_back(x, s=1.70158): x -= 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def out_elastic(x):
    if x <= 0 or x >= 1: return clamp(x)
    return 2 ** (-10 * x) * math.sin((x * 10 - .75) * 2 * math.pi / 3) + 1
def lerp(a, b, k): return a + (b - a) * k

# ---------- primitivas ----------
def fs(c, color, lw=7, alpha=1.0):
    """preenche e contorna o caminho atual"""
    c.set_source_rgba(*color, alpha); c.fill_preserve()
    c.set_source_rgba(*OL, alpha); c.set_line_width(lw); c.set_line_join(cairo.LINE_JOIN_ROUND); c.stroke()
def line(c, pts, lw=7, color=OL):
    c.move_to(*pts[0]); [c.line_to(*p) for p in pts[1:]]
    c.set_source_rgb(*color); c.set_line_width(lw); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
def rrect(c, x, y, w, h, r):
    r = min(r, w / 2, h / 2); c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi); c.close_path()
def ellipse(c, x, y, rx, ry):
    c.save(); c.translate(x, y); c.scale(rx, ry); c.new_sub_path(); c.arc(0, 0, 1, 0, 2 * math.pi); c.restore()
def sparkle(c, x, y, r, rot, color, alpha=1):
    c.save(); c.translate(x, y); c.rotate(rot); c.move_to(0, -r)
    for i in range(4):
        a1 = (i + .5) * math.pi / 2 - math.pi / 2; a2 = (i + 1) * math.pi / 2 - math.pi / 2
        c.line_to(math.cos(a1) * r * .25, math.sin(a1) * r * .25); c.line_to(math.cos(a2) * r, math.sin(a2) * r)
    c.close_path(); c.set_source_rgba(*color, alpha); c.fill(); c.restore()

# ---------- boneco ----------
def blink_at(t, seed):
    """piscadas automáticas"""
    rnd = random.Random(seed); s = rnd.uniform(.3, 1.5)
    while s < 40:
        if s <= t < s + .16: return math.sin((t - s) / .16 * math.pi)
        s += rnd.uniform(1.8, 3.6)
    return 0

def person(c, x, y, s, t, P):
    """Boneco com cabeção, olhos grandes e braços articulados. Origem = pés."""
    g = dict(skin=SKIN, hair=rgb("8a5a3b"), top=rgb("f08ca0"), bottom=rgb("4a5a8c"), coat=False, expr="smile",
             look=(0, 0), armL=.15, armR=.15, walk=None, bob=True, shake=0, item=None, bow=None, seed=1, sweat=0)
    g.update(P); P = g
    c.save(); c.translate(x, y); c.scale(s, s)
    if P["shake"]: c.translate(math.sin(t * 70) * 6 * P["shake"], 0)
    breath = math.sin(t * 2.6 + P["seed"]) * 6 if P["bob"] else 0
    ph = P["walk"]; step = math.sin(ph) if ph is not None else 0
    lift = abs(math.sin(ph)) * 18 if ph is not None else 0
    c.translate(0, -lift)
    # pernas
    for side in (-1, 1):
        a = step * .35 * side
        c.save(); c.translate(side * 45, -230); c.rotate(a)
        rrect(c, -26, 0, 52, 215, 22); fs(c, P["skin"])
        ellipse(c, side * 10, 222, 48, 24); fs(c, OL if not P["coat"] else rgb("5b4b5b"))
        c.restore()
    c.translate(0, breath * .3)
    # cabelo de trás
    hy = -720 + breath * .4
    if P["hair_back"] if "hair_back" in P else True:
        rrect(c, -192, hy - 120, 384, 400, 150); fs(c, P["hair"])
    # corpo (vestido/blusa)
    c.move_to(-95, -520); c.line_to(95, -520); c.line_to(150, -215); c.line_to(-150, -215); c.close_path()
    fs(c, P["top"])
    if P["coat"]:   # jaleco branco com lapelas
        c.move_to(-105, -525); c.line_to(105, -525); c.line_to(160, -200); c.line_to(-160, -200); c.close_path(); fs(c, WHITE)
        c.move_to(-40, -525); c.line_to(0, -430); c.line_to(40, -525); c.close_path(); fs(c, P["top"], 5)
        line(c, [(0, -430), (0, -205)], 5); c.arc(-90, -330, 0, 0, 1)
        rrect(c, 55, -330, 60, 50, 8); fs(c, WHITE, 5)
        for yy in (-380, -320, -260): ellipse(c, -18, yy, 7, 7); fs(c, rgb("d8d0d8"), 3)
    # braços
    for side, ang in ((-1, P["armL"]), (1, P["armR"])):
        c.save(); c.translate(side * 100, -500); c.rotate(ang * side * -1 if side == 1 else ang)
        c.move_to(0, 0); c.line_to(0, 200)
        c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_source_rgb(*OL); c.set_line_width(58); c.stroke_preserve()
        c.set_source_rgb(*(WHITE if P["coat"] else P["top"] if side else P["top"])); c.set_line_width(44); c.stroke()
        ellipse(c, 0, 215, 34, 34); fs(c, P["skin"])
        if P["item"] and side == 1:
            c.save(); c.translate(0, 215); P["item"](c, t); c.restore()
        c.restore()
    # pescoço + cabeça
    rrect(c, -32, -570, 64, 70, 20); fs(c, P["skin"])
    ellipse(c, 0, hy, 172, 178); fs(c, P["skin"])
    ellipse(c, -178, hy + 15, 26, 36); fs(c, P["skin"]); ellipse(c, 178, hy + 15, 26, 36); fs(c, P["skin"])
    face(c, 0, hy, t, P)
    # franja
    c.move_to(-180, hy + 10); c.curve_to(-195, hy - 230, 195, hy - 230, 180, hy + 10)
    c.curve_to(150, hy - 80, 60, hy - 120, 10, hy - 85); c.curve_to(-50, hy - 125, -150, hy - 90, -180, hy + 10)
    c.close_path(); fs(c, P["hair"])
    if P["bow"]:
        c.save(); c.translate(120, hy - 150); c.rotate(.4)
        for sd in (-1, 1): c.move_to(0, 0); c.line_to(sd * 60, -35); c.line_to(sd * 60, 35); c.close_path(); fs(c, P["bow"], 6)
        ellipse(c, 0, 0, 16, 16); fs(c, P["bow"], 6); c.restore()
    if P["sweat"]:
        k = (t * 1.3) % 1; sx, sy = -150, hy - 60 + k * 90
        c.move_to(sx, sy - 34); c.curve_to(sx + 26, sy, sx + 22, sy + 22, sx, sy + 22); c.curve_to(sx - 22, sy + 22, sx - 26, sy, sx, sy - 34)
        fs(c, rgb("9fd8ff"), 5, 1 - k * .5)
    c.restore()

def face(c, x, y, t, P):
    e = P["expr"]; lx, ly = P["look"]; bl = blink_at(t, P["seed"])
    small = e == "scared"
    for sd in (-1, 1):
        ex, ey = x + sd * 66, y + 5
        ry = 58 * (1 - bl * .92)
        ellipse(c, ex, ey, 50, max(ry, 3)); fs(c, WHITE, 6)
        if ry > 12:
            c.save(); ellipse(c, ex, ey, 50, ry); c.clip()
            ir = 22 if small else 33
            ellipse(c, ex + lx * 14, ey + ly * 14 + 6, ir, ir); fs(c, P.get("iris", rgb("4f8fd6")), 4)
            ellipse(c, ex + lx * 14, ey + ly * 14 + 6, ir * .45, ir * .45); c.set_source_rgb(*OL); c.fill()
            ellipse(c, ex + lx * 14 - ir * .35, ey + ly * 14 - ir * .3, ir * .28, ir * .28); c.set_source_rgb(*WHITE); c.fill()
            c.restore()
        # sobrancelhas
        bh = {"scared": -85, "wow": -88, "happy": -80, "sad": -70}.get(e, -74)
        tilt = {"scared": 18, "sad": 16, "angry": -16}.get(e, 0)
        line(c, [(ex - sd * 30, ey + bh - tilt), (ex + sd * 28, ey + bh + tilt * .3)], 9)
    # bochechas
    for sd in (-1, 1): ellipse(c, x + sd * 108, y + 70, 30, 18); c.set_source_rgba(*PINK, .7); c.fill()
    my = y + 98
    if e == "happy":
        c.move_to(x - 58, my - 10); c.curve_to(x - 45, my + 70, x + 45, my + 70, x + 58, my - 10); c.close_path(); fs(c, rgb("7a2335"), 6)
        c.save(); c.move_to(x - 58, my - 10); c.curve_to(x - 45, my + 70, x + 45, my + 70, x + 58, my - 10); c.close_path(); c.clip()
        ellipse(c, x, my + 52, 34, 22); c.set_source_rgb(*rgb("e8788a")); c.fill(); c.restore()
    elif e in ("scared", "wow"):
        h = 26 + (math.sin(t * 30) * 3 if e == "scared" else 0)
        ellipse(c, x, my + 8, 22 if e == "scared" else 30, h); fs(c, rgb("7a2335"), 6)
    elif e == "sad":
        c.move_to(x - 34, my + 18); c.curve_to(x - 15, my - 6, x + 15, my - 6, x + 34, my + 18)
        c.set_source_rgb(*OL); c.set_line_width(8); c.stroke()
    else:
        c.move_to(x - 36, my); c.curve_to(x - 15, my + 24, x + 15, my + 24, x + 36, my)
        c.set_source_rgb(*OL); c.set_line_width(8); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()

# ---------- objetos ----------
def mirror(c, t):
    c.save(); c.rotate(-.3)
    rrect(c, -12, 0, 24, 90, 10); fs(c, rgb("f0b6c4"), 5)
    ellipse(c, 0, -60, 62, 72); fs(c, rgb("f0b6c4"), 6); ellipse(c, 0, -60, 46, 56); fs(c, rgb("cfeefa"), 4)
    line(c, [(-20, -85), (5, -110)], 6, WHITE); c.restore()

def pen(c, t, scale=1.0):
    """Hyaluron Pen (desenho genérico de caneta sem agulha)"""
    c.save(); c.scale(scale, scale); c.rotate(-.9)
    rrect(c, -22, -40, 44, 230, 20); fs(c, rgb("f6d6de"), 6)
    rrect(c, -22, 30, 44, 50, 6); fs(c, ROSE, 5)
    c.move_to(-14, 190); c.line_to(14, 190); c.line_to(6, 240); c.line_to(-6, 240); c.close_path(); fs(c, rgb("d9d4dc"), 5)
    line(c, [(-8, -20), (-8, 10)], 5, WHITE)
    c.restore()

def syringe(c, t):
    """seringa gigante apontando para a esquerda"""
    rrect(c, 0, -70, 420, 140, 18); fs(c, rgb("e9f4fb"))
    rrect(c, 8, -55, 260, 110, 10); c.set_source_rgba(*rgb("7fc8f8"), .85); c.fill()
    for i in range(7): line(c, [(40 + i * 50, -70), (40 + i * 50, -30 if i % 2 else -10)], 6)
    rrect(c, 420, -95, 30, 190, 8); fs(c, rgb("c9d6e0"))
    rrect(c, 450, -22, 200, 44, 10); fs(c, rgb("c9d6e0"))
    rrect(c, 640, -80, 34, 160, 10); fs(c, rgb("c9d6e0"))
    c.move_to(0, -30); c.line_to(-60, -14); c.line_to(-60, 14); c.line_to(0, 30); c.close_path(); fs(c, rgb("c9d6e0"))
    c.move_to(-60, -5); c.line_to(-330, 0); c.line_to(-60, 5); c.close_path(); fs(c, rgb("dfe6ec"), 5)
    gl = (t * .8) % 1
    if gl < .4:   # brilho na agulha
        sparkle(c, -330 + gl * 600, -2, 40 * math.sin(gl / .4 * math.pi), t, WHITE)

def lips(c, puff):
    c.move_to(-280, 0)
    c.curve_to(-200, -55 - 15 * puff, -120, -125 - 25 * puff, -45, -100 - 22 * puff); c.curve_to(-22, -92 - 20 * puff, -8, -74 - 12 * puff, 0, -70 - 12 * puff)
    c.curve_to(8, -74 - 12 * puff, 22, -92 - 20 * puff, 45, -100 - 22 * puff); c.curve_to(120, -125 - 25 * puff, 200, -55 - 15 * puff, 280, 0)
    c.curve_to(190, 135 + 35 * puff, -190, 135 + 35 * puff, -280, 0); c.close_path()

# ---------- cenários ----------
def bricks(c, base, mortar, seed=2, y0=0, y1=1500):
    c.set_source_rgb(*mortar); c.rectangle(0, y0, W, y1 - y0); c.fill()
    rnd = random.Random(seed); bh, bw = 78, 170
    for r in range(int((y1 - y0) / bh) + 1):
        off = (r % 2) * bw / 2
        for i in range(-1, int(W / bw) + 2):
            v = rnd.uniform(-.05, .05); col = tuple(clamp(ch + v) for ch in base)
            rrect(c, i * bw - off + 5, y0 + r * bh + 5, bw - 10, bh - 10, 10); c.set_source_rgb(*col); c.fill()
            if rnd.random() < .2: line(c, [(i * bw - off + 30, y0 + r * bh + 22), (i * bw - off + 50, y0 + r * bh + 30)], 4, tuple(ch * .85 for ch in col))
def floor(c, col, y=1500):
    c.set_source_rgb(*col); c.rectangle(0, y, W, H - y); c.fill()
    line(c, [(0, y), (W, y)], 10)
    for i in range(1, 6): line(c, [(0, y + i * 90), (W, y + i * 90)], 4, tuple(ch * .85 for ch in col))
def window(c, x, y, w, h, sky):
    rrect(c, x, y, w, h, 14); fs(c, sky, 10)
    line(c, [(x + w / 2, y), (x + w / 2, y + h)], 10); line(c, [(x, y + h / 2), (x + w, y + h / 2)], 10)
def sunburst(c, t, c1, c2, cx=W / 2, cy=900):
    c.set_source_rgb(*c1); c.paint(); n = 18
    for i in range(n):
        a = t * .25 + i * 2 * math.pi / n
        c.move_to(cx, cy); c.arc(cx, cy, 2400, a, a + math.pi / n); c.close_path(); c.set_source_rgb(*c2); c.fill()
    rg = cairo.RadialGradient(cx, cy, 0, cx, cy, 900); rg.add_color_stop_rgba(0, 1, 1, 1, .45); rg.add_color_stop_rgba(1, 1, 1, 1, 0)
    c.set_source(rg); c.paint()

# ---------- elenco ----------
LUCIA = dict(hair=rgb("e0a040"), top=rgb("f08ca0"), iris=rgb("4f8fd6"), bow=rgb("ff6f91"), seed=3)
BRUNA = dict(hair=rgb("3a2420"), top=rgb("c0566e"), coat=True, iris=rgb("7a5230"), skin=rgb("eab894"), seed=7)

# ---------- cenas (cada uma recebe o tempo local) ----------
def cam(c, zoom, cx=W / 2, cy=H / 2, dx=0, dy=0):
    c.translate(cx + dx, cy + dy); c.scale(zoom, zoom); c.translate(-cx, -cy)

def s1_home(c, t):          # 0 – 4.5
    c.save(); cam(c, 1 + t * .025, cy=1100)
    bricks(c, rgb("e8a598"), rgb("c47f74")); floor(c, rgb("b8865a"))
    window(c, 640, 260, 300, 340, rgb("ffe3a3")); sparkle(c, 790, 330, 26, t, WHITE, .8)
    # estante
    rrect(c, 90, 520, 320, 22, 6); fs(c, rgb("9a6a44"), 6)
    for i, col in enumerate(["ff8fab", "8fd3ff", "ffd166"]): rrect(c, 110 + i * 95, 430, 70, 90, 14); fs(c, rgb(col), 6)
    look = (.6, -.2) if t < 2.4 else (.2, .2)
    expr = "smile" if t < 2.2 else "sad"
    person(c, 520, 1560, 1.0, t, dict(LUCIA, expr=expr, look=look, armR=1.9 + math.sin(t * 2) * .05, item=mirror))
    if t > 2.3:   # balão de pensamento com lábios
        k = out_back(prog(t, 2.3, 2.8))
        c.save(); c.translate(820, 640); c.scale(k, k)
        for (bx, by, br) in [(-150, 170, 16), (-110, 120, 26)]: ellipse(c, bx, by, br, br); fs(c, WHITE, 6)
        ellipse(c, 40, 0, 170, 120); fs(c, WHITE, 7)
        c.save(); c.translate(40, 10); c.scale(.42 + .04 * math.sin(t * 5), .42 + .04 * math.sin(t * 5)); lips(c, 1)
        g = cairo.LinearGradient(0, -120, 0, 150); g.add_color_stop_rgb(0, *rgb("e05a7a")); g.add_color_stop_rgb(1, *rgb("a8324f"))
        c.set_source(g); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(14); c.stroke(); c.restore()
        c.restore()
    c.restore()

def s2_fear(c, t):          # 4.5 – 9
    c.set_source_rgb(*rgb("2a2238")); c.paint()
    rg = cairo.RadialGradient(400, 1400, 50, 400, 1400, 900); rg.add_color_stop_rgba(0, 1, .9, .7, .35); rg.add_color_stop_rgba(1, 1, .9, .7, 0)
    c.set_source(rg); c.paint()
    zoom = 1 + out_cubic(prog(t, 1.4, 2.0)) * .18
    c.save(); cam(c, zoom, cx=380, cy=900)
    ellipse(c, 400, 1580, 300, 50); c.set_source_rgba(0, 0, 0, .35); c.fill()
    scared = t > 1.0
    person(c, 400, 1570, .95, t, dict(LUCIA, expr="scared" if scared else "wow", look=(.8, -.1), armL=.6 if scared else .15,
                                       armR=.6 if scared else .15, shake=1 if scared else 0, sweat=scared))
    c.restore()
    k = out_back(prog(t, .4, 1.1), 1.2)
    sx = lerp(W + 900, 690, k)
    c.save(); c.translate(sx, 760); c.rotate(math.sin(t * 3) * .05 - .25); c.scale(1.05, 1.05); syringe(c, t); c.restore()
    for i in range(3):   # tracinhos de susto
        kk = prog(t, 1.0 + i * .08, 1.25 + i * .08)
        if 0 < kk < 1 or t > 1.25:
            a = -2.2 + i * .45; r0 = 300
            line(c, [(400 + math.cos(a) * r0, 830 + math.sin(a) * r0), (400 + math.cos(a) * (r0 + 70), 830 + math.sin(a) * (r0 + 70))], 12, YELLOW)

def clinic_bg(c, t):
    c.set_source_rgb(*rgb("fbe4e6")); c.paint()
    for i in range(0, W, 120): c.rectangle(i, 0, 60, 1500); c.set_source_rgba(1, 1, 1, .45); c.fill()
    rrect(c, 0, 1080, W, 30, 0); fs(c, rgb("e7b7c0"), 6)
    floor(c, rgb("f1d3b3"))
    # quadro com o logo
    rrect(c, 330, 230, 420, 380, 30); fs(c, WHITE, 10)
    if LOGO_SURF:
        c.save(); c.translate(540, 420); s = .58; c.scale(s, s); c.translate(-LOGO_SURF.get_width() / 2, -LOGO_SURF.get_height() / 2)
        c.set_source_rgb(*ROSE_D); c.mask_surface(LOGO_SURF); c.restore()
    # planta
    for a in (-.6, -.2, .2, .6):
        c.save(); c.translate(960, 1380); c.rotate(a + math.sin(t * 1.5 + a) * .04); ellipse(c, 0, -120, 34, 110); fs(c, rgb("7cc58a"), 6); c.restore()
    rrect(c, 900, 1360, 120, 140, 16); fs(c, rgb("f6c9a8"), 7)

def s3_clinic(c, t):        # 9 – 13.5
    c.save(); cam(c, 1.02 + t * .015, cy=1200)
    clinic_bg(c, t)
    k = out_cubic(prog(t, .1, 1.6)); bx = lerp(W + 250, 760, k)
    walking = k < 1
    wave = max(0, math.sin((t - 1.6) * 7)) if t > 1.6 else 0
    person(c, bx, 1580, .92, t, dict(BRUNA, expr="happy" if t > 1.4 else "smile", look=(-.7, 0), walk=t * 9 if walking else None,
                                      armL=.15 if t < 2.6 else 1.2, armR=(2.3 + wave * .5) if 1.6 < t < 2.6 else (1.0 if t >= 2.6 else .2),
                                      item=(lambda c, tt: pen(c, tt, 1.0)) if t >= 2.6 else None))
    look = (.8, 0) if t < 2.6 else (.9, -.4)
    expr = "scared" if t < 1.6 else ("wow" if t < 2.8 else "happy")
    person(c, 300, 1580, .92, t, dict(LUCIA, expr=expr, look=look, armL=.2, armR=.2, sweat=t < 1.6))
    if t > 2.6:   # brilhos em volta da caneta
        for i in range(4):
            kk = out_back(prog(t, 2.7 + i * .12, 3.1 + i * .12), 3)
            if kk > 0: sparkle(c, 640 + math.cos(i * 1.7) * 140, 980 + math.sin(i * 2.3) * 120, 34 * kk, t * 2 + i, YELLOW)
    c.restore()

def s4_lips(c, t):          # 13.5 – 18
    c.set_source_rgb(*rgb("f7d9df")); c.paint()
    rg = cairo.RadialGradient(W / 2, 900, 0, W / 2, 900, 800); rg.add_color_stop_rgba(0, 1, 1, 1, .7); rg.add_color_stop_rgba(1, 1, 1, 1, 0)
    c.set_source(rg); c.paint()
    # rosto em close (queixo e nariz)
    c.save(); c.translate(W / 2, 960); zz = 1 + t * .02; c.scale(zz, zz)
    ellipse(c, 0, 60, 640, 800); fs(c, SKIN, 10)
    c.move_to(-40, -360); c.curve_to(-60, -250, -70, -200, -40, -190); c.curve_to(-15, -175, 15, -175, 40, -190)
    c.set_source_rgb(*SKIN2); c.set_line_width(9); c.set_line_cap(cairo.LINE_CAP_ROUND); c.stroke()
    for sd in (-1, 1): ellipse(c, sd * 290, -120, 80, 46); c.set_source_rgba(*PINK, .6); c.fill()
    puff = 0
    for i, t0 in enumerate((.9, 1.6, 2.3)):
        puff += out_elastic(prog(t, t0, t0 + .6)) / 3
    c.save(); c.translate(0, 80); s = .85 + puff * .05; c.scale(s, s); lips(c, puff)
    g = cairo.LinearGradient(0, -150, 0, 170); g.add_color_stop_rgb(0, *rgb("e46f8a")); g.add_color_stop_rgb(1, *rgb("b23a58"))
    c.set_source(g); c.fill_preserve(); c.set_source_rgb(*OL); c.set_line_width(12); c.stroke()
    c.move_to(-280, 0); c.curve_to(-150, 24, 150, 24, 280, 0); c.set_line_width(9); c.stroke()
    ellipse(c, -90, 60 + puff * 15, 60, 16); c.set_source_rgba(1, 1, 1, .45); c.fill()
    c.restore()
    for i, t0 in enumerate((.9, 1.6, 2.3)):   # sopros de ar da caneta (anéis)
        k = prog(t, t0 - .1, t0 + .5)
        if 0 < k < 1:
            px, py = [(-140, 40), (140, 40), (0, 150)][i]
            for j in range(3):
                kk = clamp(k * 1.4 - j * .2)
                if kk > 0: ellipse(c, px, py, 40 + kk * 120, 20 + kk * 60); c.set_source_rgba(1, 1, 1, .8 * (1 - kk)); c.set_line_width(8); c.stroke()
    for i in range(6):
        kk = out_back(prog(t, 2.6 + i * .1, 3.0 + i * .1), 3)
        if kk > 0: sparkle(c, math.cos(i * 1.05) * 400, 80 + math.sin(i * 1.05) * 260, 44 * kk, t * 1.5 + i, YELLOW)
    c.restore()
    # caneta entrando e apontando para os lábios, pulando a cada disparo
    targets = [(-140, 40), (140, 40), (0, 150)]
    idx = 0 if t < 1.4 else 1 if t < 2.1 else 2
    tx, ty = targets[idx]
    k = out_cubic(prog(t, .2, .8)); hop = sum(max(0, 1 - abs(t - t0) * 8) for t0 in (.9, 1.6, 2.3)) * 30
    away = in_out(prog(t, 3.2, 3.8))
    px = lerp(W + 400, W / 2 + tx + 305, k) + away * 700; py = lerp(100, 1040 + ty * .85 - 305, k) - hop - away * 500
    c.save(); c.translate(px, py); c.rotate(1.685); pen(c, t, 1.8); c.restore()

def s5_happy(c, t):         # 18 – 21.5
    sunburst(c, t, rgb("ffb3c6"), rgb("ff9bb5"))
    jump = abs(math.sin(t * 5.2)) * 120 if t > .3 else 0
    sq = 1 - .06 * max(0, math.cos(t * 5.2 * 2)) if t > .3 else 1
    c.save(); c.translate(W / 2, 1600); c.scale(1 / sq, sq); c.translate(-W / 2, -1600)
    ellipse(c, W / 2, 1610, 260 - jump * .6, 40); c.set_source_rgba(.5, .2, .3, .25); c.fill()
    person(c, W / 2, 1600 - jump, 1.05, t, dict(LUCIA, expr="happy", look=(0, -.3), armL=2.6 + math.sin(t * 10) * .2,
                                                   armR=2.6 + math.sin(t * 10 + 1) * .2, bob=False))
    c.restore()
    rnd = random.Random(9)   # confetes caindo
    for i in range(60):
        x0, sp, ph, col = rnd.uniform(0, W), rnd.uniform(300, 600), rnd.uniform(0, 1), rnd.choice(["ffd23f", "ffffff", "c0566e", "7cc58a", "8fd3ff"])
        y = -60 + (t * sp + ph * 400) - 300 * (1 - prog(t, 0, .4)); x = x0 + math.sin(t * 3 + i) * 40
        if y < -50 or y > H: continue
        c.save(); c.translate(x, y); c.rotate(t * 4 + i); c.scale(1, abs(math.sin(t * 6 + i)) + .2)
        c.rectangle(-12, -7, 24, 14); c.set_source_rgb(*rgb(col)); c.fill(); c.restore()
    for i in range(3):
        sparkle(c, 200 + i * 340, 420 + (i % 2) * 120, 50 * (1 + .2 * math.sin(t * 6 + i)), t + i, WHITE)

def s6_end(c, t):           # 21.5 – 24.5
    c.set_source_rgb(*rgb("fbe4e6")); c.paint()
    sunburst(c, t * .5, rgb("fbe4e6"), rgb("f8d6dc"), cy=700)
    k = out_elastic(prog(t, .1, 1.0))
    if LOGO_SURF and k > 0:
        c.save(); c.translate(W / 2, 640); c.rotate((1 - k) * .5); s = 1.05 * k; c.scale(s, s)
        c.translate(-LOGO_SURF.get_width() / 2, -LOGO_SURF.get_height() / 2); c.set_source_rgb(*ROSE_D); c.mask_surface(LOGO_SURF); c.restore()
    kb = out_back(prog(t, .6, 1.1))
    if kb > 0:
        pulse = 1 + .04 * math.sin(t * 7) * clamp(t - 1.2)
        c.save(); c.translate(W / 2, 1060); c.scale(kb * pulse, kb * pulse)
        rrect(c, -330, -75, 660, 150, 75); fs(c, ROSE, 9)
        font(c, 62); s = "Reserva tu cita"; c.set_source_rgb(*WHITE); c.move_to(-tw(c, s) / 2, 22); c.show_text(s); c.restore()
    for i, (P, x, d) in enumerate([(LUCIA, 300, .9), (BRUNA, 780, 1.1)]):
        kk = out_back(prog(t, .9 + i * .15, 1.4 + i * .15))
        y = 2500 - kk * 650
        wave = 2.4 + math.sin(t * 8 + i) * .4
        person(c, x, y, .78, t + i, dict(P, expr="happy", look=(.3 if i == 0 else -.3, .2), armR=wave if i == 0 else 1.0,
                                           armL=.2 if i == 0 else wave, item=None))

SCENES = [(0, 4.5, s1_home), (4.5, 9.0, s2_fear), (9.0, 13.5, s3_clinic), (13.5, 18.0, s4_lips), (18.0, 21.5, s5_happy), (21.5, DUR, s6_end)]
WHIPS = {9.0, 18.0, 21.5}         # transições em chicote; as outras são corte seco com "punch"

# ---------- legendas ----------
CAPS = [(.4, 2.1, "Lucía soñaba con"), (2.1, 4.4, "unos labios con *más volumen*"),
        (4.7, 6.3, "pero le daban"), (6.3, 8.9, "*pánico* las agujas"),
        (9.3, 11.2, "Hasta que Bruna"), (11.2, 13.4, "le presentó el *Hyaluron Pen*"),
        (13.8, 15.7, "*Sin agujas.*"), (15.7, 17.9, "Volumen sutil y *natural*"),
        (18.3, 21.3, "¡Y ahora no para de *sonreír!*")]
def font(c, size): c.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD); c.set_font_size(size)
def tw(c, s): return c.text_extents(s).x_advance
def captions(c, t):
    for a, b, text in CAPS:
        if not (a <= t < b): continue
        toks, hl = [], False
        for w in text.split(" "):
            st = w.startswith("*"); en = w.endswith("*")
            if st: hl = True
            toks.append((w.strip("*"), hl))
            if en: hl = False
        font(c, 84); sp = tw(c, " ") + 16; lines, cur, cw = [], [], 0
        for i, (w, h) in enumerate(toks):
            ww = tw(c, w)
            if cur and cw + sp + ww > 900: lines.append((cur, cw)); cur, cw = [], 0
            cur.append((i, w, h, ww)); cw += (sp if len(cur) > 1 else 0) + ww
        lines.append((cur, cw))
        y = 1700 - (len(lines) - 1) * 50
        for ln, lw in lines:
            x = W / 2 - lw / 2
            for i, w, h, ww in ln:
                k = out_back(prog(t, a + i * .1, a + i * .1 + .25), 2.2)
                if k > 0:
                    c.save(); c.translate(x + ww / 2, y - 30); c.scale(k, k); c.translate(-ww / 2, 30)
                    c.move_to(0, 0); c.text_path(w)
                    c.set_line_join(cairo.LINE_JOIN_ROUND); c.set_source_rgb(*OL); c.set_line_width(16); c.stroke_preserve()
                    c.set_source_rgb(*(YELLOW if h else WHITE)); c.fill(); c.restore()
                x += ww + sp
            y += 100

# ---------- montagem do quadro ----------
def scene_at(t):
    for a, b, fn in SCENES:
        if a <= t < b: return a, fn
    return SCENES[-1][0], SCENES[-1][2]

def render_scene(t, dx=0):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
    a, fn = scene_at(t); c.translate(dx, 0); fn(c, t - a); return surf

def frame(t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
    whip = next((w for w in WHIPS if abs(t - w) < .2), None)
    if whip is not None:
        k = in_out(prog(t, whip - .2, whip + .2)); off = k * W
        A = render_scene(whip - .001); B = render_scene(whip + .001 + max(0, t - whip))
        if t < whip: A = render_scene(t)
        c.set_source_surface(A, -off, 0); c.paint(); c.set_source_surface(B, W - off, 0); c.paint()
        surf.flush()
        arr = np.ndarray((H, W, 4), np.uint8, surf.get_data()).copy()
        im = Image.fromarray(arr); strength = math.sin(k * math.pi)
        blur = im.resize((max(8, int(W / (1 + 40 * strength))), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
        arr = np.asarray(Image.blend(im, blur, min(1, strength * 1.5))).copy()
        surf = cairo.ImageSurface.create_for_data(memoryview(arr), cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
        global _KEEP; _KEEP = arr          # mantém o buffer vivo
    else:
        a, fn = scene_at(t)
        punch = 1 + .06 * (1 - out_cubic(prog(t - a, 0, .3))) if a in (4.5, 13.5) else 1   # "soco" de zoom no corte
        c.save(); cam(c, punch); fn(c, t - a); c.restore()
    captions(c, t)
    fo = max(1 - prog(t, 0, .3), prog(t, DUR - .4, DUR))
    if fo > 0: c.set_source_rgba(0, 0, 0, fo); c.paint()
    surf.flush(); return surf

# ---------- áudio: trilha alegre + efeitos ----------
def audio(path):
    SR = 44100; n = int(DUR * SR); L = np.zeros(n); R = np.zeros(n); rng = np.random.default_rng(5)
    def hz(m): return 440 * 2 ** ((m - 69) / 12)
    def add(sig, st, pan=.5, g=1.0):
        s = int(st * SR); e = min(n, s + len(sig))
        if s >= n or e <= s: return
        L[s:e] += sig[:e - s] * g * (1 - pan); R[s:e] += sig[:e - s] * g * pan
    def pluck(m, d=.6, bright=1.0):
        tt = np.arange(int(d * SR)) / SR; f = hz(m)
        return (np.sin(2 * np.pi * f * tt) + .5 * bright * np.sin(4 * np.pi * f * tt) + .25 * bright * np.sin(6 * np.pi * f * tt)) * np.exp(-tt * 7) * np.minimum(tt / .004, 1)
    bpm = 112; beat = 60 / bpm
    prog_ = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]   # C – G – Am – F
    melody = [72, 74, 76, 79, 76, 74, 72, 67, 71, 74, 72, 71, 69, 72, 76, 74]
    t0 = 0.0; b = 0
    while t0 < DUR - .5:
        ch = prog_[(b // 4) % 4]
        if (b // 4) * 4 * beat < 4.5 or True:
            dark = 4.5 <= t0 < 9.0                  # na cena do medo a música fica tensa (só baixo pulsando)
            add(pluck(ch[0] - 24, .5, .3), t0, .5, .22)
            if not dark:
                for j, m in enumerate(ch): add(pluck(m, .45, .6), t0 + beat / 2, .3 + .2 * j, .07)
                if b % 2 == 0: add(pluck(melody[(b // 2) % 16], .5), t0, .6, .09)
                sh = rng.standard_normal(int(.05 * SR)) * np.exp(-np.arange(int(.05 * SR)) / SR * 80); add(sh, t0 + beat / 2, .7, .03)
            else:
                add(pluck(ch[0] - 23, .3, .2), t0 + beat / 2, .5, .15)
        t0 += beat; b += 1
    def whoosh(d=.45):
        m = int(d * SR); x = rng.standard_normal(m); env = np.sin(np.linspace(0, np.pi, m)) ** 2
        y = np.convolve(x, np.ones(12) / 12, "same"); return y * env
    def pop(f0=900, d=.09):
        tt = np.arange(int(d * SR)) / SR; f = f0 * np.exp(-tt * 18); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 30)
    def chime(f=1760, d=1.0):
        tt = np.arange(int(d * SR)) / SR; return (np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * f * 2.76 * tt)) * np.exp(-tt * 5)
    def boing(d=.4):
        tt = np.arange(int(d * SR)) / SR; f = 220 + 160 * np.sin(tt * 40) * np.exp(-tt * 6); return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 6)
    for w in sorted(WHIPS): add(whoosh(), w - .22, .5, .35)
    for a, b_, text in CAPS:
        for i, _ in enumerate(text.split(" ")): add(pop(1100 + 80 * i), a + i * .1, .5, .05)
    add(boing(), 4.5 + .7, .7, .3)                                  # seringa chegando
    tt = np.arange(int(1.6 * SR)) / SR; add(np.sin(2 * np.pi * (60 + 20 * tt) * tt) * np.exp(-tt * 2), 4.5 + 1.0, .5, .25)  # susto grave
    for i in range(4): add(chime(1568 * 2 ** (i / 12 * 3)), 9.0 + 2.7 + i * .12, .3 + i * .15, .08)
    for t_ in (.9, 1.6, 2.3):
        m = int(.25 * SR); add(np.convolve(rng.standard_normal(m), np.ones(4) / 4, "same") * np.exp(-np.arange(m) / SR * 18), 13.5 + t_, .5, .12)  # "pff" da caneta
        add(pop(500, .15), 13.5 + t_ + .05, .5, .1)
    for i in range(6): add(chime(2093 * 2 ** (i / 12 * 2)), 13.5 + 2.6 + i * .1, .2 + i * .12, .06)
    for j in range(5): add(boing(.3), 18.3 + j * (math.pi / 5.2), .5, .12)
    add(chime(1046, 1.6), 21.6, .5, .15); add(chime(1318, 1.6), 21.7, .5, .12)
    mix = np.stack([L, R], 1); mix *= .9 / max(1e-6, np.abs(mix).max())
    fade = np.minimum(1, (n - np.arange(n)) / (SR * .8)); mix *= fade[:, None]
    with wave.open(path, "wb") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes((mix * 32767).astype("<i2").tobytes())

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "video"
    if mode == "preview":
        os.makedirs(sys.argv[2], exist_ok=True)
        for ts in sys.argv[3:]: frame(float(ts)).write_to_png(os.path.join(sys.argv[2], f"t{float(ts):05.2f}.png"))
    elif mode == "audio": audio(sys.argv[2])
    else:
        out = sys.stdout.buffer
        for i in range(int(DUR * FPS)): out.write(bytes(frame(i / FPS).get_data()))
