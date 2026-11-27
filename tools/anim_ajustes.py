"""Flor de Lótus · vídeo animado "Como funcionam os ajustes" (vestido e terno).

Uso: python3 tools/anim_ajustes.py SAIDA.mp4 [DURACAO_MAX]
Gera só o vídeo (sem áudio); o áudio é montado em tools/anim_ajustes_audio.sh.
"""
import math
import subprocess
import sys
from multiprocessing import Pool

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = "/home/user/Edi-o-de-v-deo-/edita-ai/"
F = ROOT + "fonts/"
LOGO = ROOT + "flor_lotus/logo_transparente.png"

W, H, FPS = 1080, 1920, 30
S = 2  # supersampling
DUR = 28.5

FUNDO = (14, 12, 13)
BRANCO = (255, 255, 255)
ROSA = (212, 140, 140)
ROSA_SUAVE = (150, 108, 110)
CINZA = (200, 192, 192)

_fc = {}


def font(name, size):
    key = (name, size)
    if key not in _fc:
        path = {
            "pf": F + "playfair-display-latin-700-normal.ttf",
            "pfi": F + "playfair-display-latin-700-italic.ttf",
            "pf6": F + "playfair-display-latin-600-normal.ttf",
            "pf6i": F + "playfair-display-latin-600-italic.ttf",
            "inter": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
            "inter6": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
            "mont": F + "montserrat-latin-500-normal.ttf",
            "mont7": F + "montserrat-latin-700-normal.ttf",
        }[name]
        _fc[key] = ImageFont.truetype(path, int(size * S))
    return _fc[key]


# ---------------------------------------------------------------- tempo

def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(p):
    p = clamp(p)
    return 1 - (1 - p) ** 3


def prog(t, t0, dur):
    return clamp((t - t0) / dur)


def fade(t, t_in, t_out=None, d_in=0.25, d_out=0.25):
    a = ease(prog(t, t_in, d_in))
    if t_out is not None:
        a *= 1 - ease(prog(t, t_out, d_out))
    return a


# ---------------------------------------------------------------- desenho

def quad(p0, c, p1, n=24):
    pts = []
    for i in range(n + 1):
        u = i / n
        x = (1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u ** 2 * p1[0]
        y = (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u ** 2 * p1[1]
        pts.append((x, y))
    return pts


def seg(*pts):
    return list(pts)


K = 1.0


def tf(pts, dx=0):
    return [(540 + (x - 330) * K + dx, 470 + (y - 500) * K) for x, y in pts]


HANGER = [
    quad((318, 498), (330, 474), (342, 494), 12),
    seg((342, 494), (330, 532)),
    seg((250, 580), (330, 532), (410, 580)),
    seg((250, 580), (410, 580)),
]

VESTIDO = {
    "base": HANGER + [
        quad((290, 672), (330, 722), (370, 672)),
        quad((290, 672), (272, 742), (300, 805)),
        quad((370, 672), (388, 742), (360, 805)),
        quad((300, 805), (268, 1000), (200, 1225)),
        quad((360, 805), (392, 1000), (460, 1225)),
    ],
    "fino": [
        quad((318, 812), (300, 1000), (268, 1240)),
        quad((342, 812), (366, 1000), (392, 1240)),
    ],
    "barra": [quad((200, 1225), (330, 1262), (460, 1225))],
    "alca": [seg((292, 579), (290, 672)), seg((368, 579), (370, 672))],
    "cintura": [quad((300, 805), (330, 813), (360, 805))],
}
SETAS_VESTIDO = [((262, 808), (292, 808)), ((398, 808), (368, 808))]

TERNO = {
    "base": HANGER + [
        seg((305, 560), (355, 560)),
        seg((305, 560), (245, 590)),
        seg((355, 560), (415, 590)),
        seg((305, 560), (318, 602), (298, 622), (330, 760)),
        seg((355, 560), (342, 602), (362, 622), (330, 760)),
        seg((245, 590), (250, 892)),
        seg((415, 590), (410, 892)),
        seg((330, 760), (330, 880)),
        quad((330, 880), (326, 896), (316, 902), 8),
        quad((330, 880), (334, 896), (344, 902), 8),
        seg((250, 892), (316, 902)),
        seg((344, 902), (410, 892)),
        seg((245, 590), (212, 850)),
        seg((262, 660), (240, 855)),
        seg((415, 590), (448, 850)),
        seg((398, 660), (420, 855)),
        seg((262, 832), (300, 835)),
        seg((360, 835), (398, 832)),
        # calça
        seg((268, 912), (392, 912)),
        seg((268, 930), (392, 930)),
        seg((268, 912), (268, 930)),
        seg((392, 912), (392, 930)),
        seg((268, 930), (262, 1232)),
        seg((330, 930), (330, 978)),
        seg((330, 978), (324, 1232)),
        seg((392, 930), (398, 1232)),
        seg((330, 978), (336, 1232)),
    ],
    "fino": [],
    "punho": [
        seg((212, 850), (209, 876), (238, 881), (240, 855), (212, 850)),
        seg((448, 850), (451, 876), (422, 881), (420, 855), (448, 850)),
    ],
    "barra_calca": [seg((262, 1232), (324, 1232)), seg((336, 1232), (398, 1232))],
    "pinca": [seg((286, 735), (289, 812)), seg((374, 735), (371, 812))],
}
BOTOES = [(337, 792), (337, 836)]
SETAS_TERNO = [((256, 775), (280, 775)), ((404, 775), (380, 775))]


def plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def partial(pts, p):
    if p >= 1:
        return pts
    if p <= 0:
        return pts[:1]
    total = plen(pts) * p
    out = [pts[0]]
    acc = 0.0
    for i in range(len(pts) - 1):
        d = math.dist(pts[i], pts[i + 1])
        if acc + d >= total:
            u = (total - acc) / d if d else 0
            out.append((pts[i][0] + (pts[i + 1][0] - pts[i][0]) * u,
                        pts[i][1] + (pts[i + 1][1] - pts[i][1]) * u))
            return out
        acc += d
        out.append(pts[i + 1])
    return out


def sc(pts):
    return [(x * S, y * S) for x, y in pts]


def line(d, pts, col, width, alpha=1.0):
    if len(pts) < 2:
        return
    c = col + (int(255 * alpha),)
    d.line(sc(pts), fill=c, width=int(width * S), joint="curve")
    r = width * S / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), fill=c)


def arrow(d, a, b, col, alpha, p):
    if p <= 0:
        return
    b2 = (a[0] + (b[0] - a[0]) * p, a[1] + (b[1] - a[1]) * p)
    line(d, [a, b2], col, 3, alpha)
    ang = math.atan2(b2[1] - a[1], b2[0] - a[0])
    for s in (2.5, -2.5):
        tip = (b2[0] - 11 * math.cos(ang + s), b2[1] - 11 * math.sin(ang + s))
        line(d, [b2, tip], col, 3, alpha)


# ---------------------------------------------------------------- texto

def text_parts(d, y, parts, size, alpha=1.0, cx=540, x0=None, fonts=("pf", "pfi")):
    """parts: lista de (texto, destaque). Centraliza em cx (ou começa em x0)."""
    fs = [font(fonts[1] if hl else fonts[0], size) for _, hl in parts]
    ws = [d.textlength(t, font=f) for (t, _), f in zip(parts, fs)]
    x = x0 * S if x0 is not None else cx * S - sum(ws) / 2
    for (t, hl), f, w in zip(parts, fs, ws):
        col = (ROSA if hl else BRANCO) + (int(255 * alpha),)
        d.text((x, y * S), t, font=f, fill=col, anchor="ls")
        x += w


def spaced(d, cx, y, txt, size, col, alpha, spacing=0.22, fname="inter"):
    f = font(fname, size)
    ws = [d.textlength(ch, font=f) for ch in txt]
    total = sum(ws) + spacing * size * S * (len(txt) - 1)
    x = cx * S - total / 2
    for ch, w in zip(txt, ws):
        d.text((x, y * S), ch, font=f, fill=col + (int(255 * alpha),), anchor="ls")
        x += w + spacing * size * S


def layer():
    im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


# ---------------------------------------------------------------- fundo

def make_bg():
    bg = Image.new("RGB", (W, H), FUNDO)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((-200, 300, W + 200, 1700), fill=40)
    glow = glow.filter(ImageFilter.GaussianBlur(220))
    warm = Image.new("RGB", (W, H), (46, 34, 37))
    bg = Image.composite(warm, bg, glow)
    d = ImageDraw.Draw(bg, "RGBA")
    # fios finos (visual Dourado)
    d.rectangle((54, 54, W - 54, H - 54), outline=ROSA + (60,), width=2)
    return bg.convert("RGBA")


BG = None
LOGO_IM = None


# ---------------------------------------------------------------- cenas

def draw_garment(d, gl, t, g, t_draw, items, t_out, dx_out):
    """g: dicionário de partes; items: lista de (nome_parte, t_item)."""
    a_out = 1 - ease(prog(t, t_out, 0.3)) if t_out else 1
    if a_out <= 0:
        return
    dx = -60 * ease(prog(t, t_out, 0.3)) if t_out else 0
    p = ease(prog(t, t_draw, 1.3))
    for pts in g["base"]:
        line(d, partial(tf(pts, dx), p), BRANCO, 3.2, 0.92 * a_out)
    for pts in g["fino"]:
        line(d, partial(tf(pts, dx), p), BRANCO, 1.8, 0.45 * a_out)
    for name, ti in items:
        for pts in g[name]:
            line(d, partial(tf(pts, dx), p), BRANCO, 3.2, 0.92 * a_out)
        hp = prog(t, ti, 0.4)
        if hp > 0:
            pulse = 1 + 0.6 * math.sin(math.pi * clamp((t - ti) / 0.6)) if t - ti < 0.6 else 1
            for pts in g[name]:
                pp = partial(tf(pts, dx), ease(hp))
                line(d, pp, ROSA, 5.5 * pulse, a_out)
                line(gl, pp, ROSA, 16 * pulse, 0.9 * a_out)
    return dx, a_out, p


def check_row(d, t, ti, y, label, a_out=1.0, x=318):
    p = prog(t, ti, 0.2)
    if p <= 0:
        return
    a = ease(p) * a_out
    off = -40 * (1 - ease(p))
    cx, cy, r = x + 24 + off, y - 18, 24
    # círculo do check se desenhando
    pc = ease(prog(t, ti + 0.05, 0.2))
    if pc > 0:
        d.arc(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), -90, -90 + 360 * pc,
              fill=ROSA + (int(255 * a),), width=int(3 * S))
    pk = ease(prog(t, ti + 0.2, 0.15))
    if pk > 0:
        pts = [(cx - 10, cy + 1), (cx - 3, cy + 8), (cx + 11, cy - 8)]
        line(d, partial(pts, pk), ROSA, 3.6, a)
    text_parts(d, y, [(label, False)], 54, a, x0=x + 66 + off, fonts=("pf6", "pf6i"))


def title_block(d, t, t_in, t_out, etiqueta, parts):
    a = fade(t, t_in, t_out, 0.3, 0.3)
    if a <= 0:
        return
    up = 14 * (1 - ease(prog(t, t_in, 0.3)))
    spaced(d, 540, 300 + up, etiqueta, 28, ROSA, a)
    text_parts(d, 400 + up, parts, 84, a)


def scene_hook(d, t):
    if t > 3.3:
        return
    a_out = 1 - ease(prog(t, 3.0, 0.25))
    # entrada em 4 quadros crescendo de 90% a 100%
    p = ease(prog(t, 0.0, 0.13))
    a = p * a_out
    up = -20 * ease(prog(t, 3.0, 0.25))
    s = 0.9 + 0.1 * p
    tmp, td = layer()
    text_parts(td, 640, [("O vestido ficou", False)], 104, 1.0)
    text_parts(td, 770, [("grande", True), ("?", False)], 120, 1.0)
    a2 = fade(t, 1.5, None, 0.3) * a_out
    text_parts(td, 960, [("A gente ", False), ("ajusta", True), (".", False)], 78, a2,
               fonts=("pf6", "pf6i"))
    # linha fina
    lp = ease(prog(t, 1.6, 0.4))
    if lp > 0:
        line(td, [(540 - 120 * lp, 1030), (540 + 120 * lp, 1030)], ROSA, 2, a2)
    if s != 1:
        tmp = tmp.resize((int(W * S * s), int(H * S * s)), Image.BILINEAR)
        big = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        big.paste(tmp, ((W * S - tmp.width) // 2, (H * S - tmp.height) // 2 - int(150 * S * (1 - s))))
        tmp = big
    if a < 1:
        al = tmp.split()[3].point(lambda v: int(v * a))
        tmp.putalpha(al)
    return tmp, up


def scene_stamp(d, base, t):
    t0, t_out = 17.3, 20.8
    if t < t0 or t > t_out + 0.35:
        return
    a = fade(t, t0, t_out, 0.3, 0.3)
    text_parts(d, 640, [("Todos os ", False), ("ajustes", True)], 92, a)
    text_parts(d, 735, [("do vestido e do terno", False)], 52, a * 0.9, fonts=("pf6", "pf6i"))
    # carimbo
    ts = 17.9
    if t >= ts:
        p = prog(t, ts, 0.18)
        if p < 0.75:
            s = 1.6 - (1.6 - 0.95) * ease(p / 0.75)
        else:
            s = 0.95 + 0.05 * ease((p - 0.75) / 0.25)
        aa = clamp((t - ts) / 0.08) * (1 - ease(prog(t, t_out, 0.3)))
        st = Image.new("RGBA", (760 * S, 300 * S), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((10 * S, 10 * S, 750 * S, 290 * S), 18 * S, outline=ROSA + (255,), width=9 * S)
        f1 = font("inter", 104)
        f2 = font("inter", 46)
        sd.text((380 * S, 150 * S), "INCLUSO", font=f1, fill=ROSA + (255,), anchor="ms")
        sd.text((380 * S, 232 * S), "NO ALUGUEL", font=f2, fill=ROSA + (255,), anchor="ms")
        st = st.rotate(8, resample=Image.BICUBIC, expand=True)
        st = st.resize((int(st.width * s), int(st.height * s)), Image.BICUBIC)
        if aa < 1:
            st.putalpha(st.split()[3].point(lambda v: int(v * aa)))
        base.alpha_composite(st, (540 * S - st.width // 2, 980 * S - st.height // 2))


def scene_count(d, t):
    t0, t_out = 21.1, 24.8
    if t < t0 or t > t_out + 0.35:
        return
    a = fade(t, t0, t_out, 0.3, 0.3)
    text_parts(d, 560, [("Faça sua ", False), ("prova", True)], 84, a)
    text_parts(d, 640, [("com até", False)], 54, a * 0.9, fonts=("pf6", "pf6i"))
    n = round(15 * ease(prog(t, 21.4, 0.8)))
    f = font("pfi", 340)
    d.text((540 * S, 960 * S), f"{n:02d}", font=f, fill=ROSA + (int(255 * a),), anchor="ms")
    text_parts(d, 1080, [("dias antes", False)], 84, a)
    a2 = fade(t, 22.4, t_out, 0.3, 0.3)
    spaced(d, 540, 1170, "DA RETIRADA DO TRAJE", 30, CINZA, a2, 0.18, "inter6")
    text_parts(d, 1290, [("assim dá tempo de deixar ", False), ("perfeito", True)], 46, a2,
               fonts=("pf6", "pf6i"))


def scene_final(base, t):
    t0 = 25.1
    if t < t0:
        return
    p = ease(prog(t, t0, 0.4))
    cx0, cy0, cx1, cy1 = 140, 640, 940, 1280
    dy = int(40 * (1 - p))
    card, cd = layer()
    shadow, shd = layer()
    shd.rounded_rectangle((cx0 * S, (cy0 + 10 + dy) * S, cx1 * S, (cy1 + 10 + dy) * S), 28 * S, fill=(0, 0, 0, 120))
    shadow = shadow.resize((W, H)).filter(ImageFilter.GaussianBlur(16)).resize((W * S, H * S))
    cd.rounded_rectangle((cx0 * S, (cy0 + dy) * S, cx1 * S, (cy1 + dy) * S), 28 * S, fill=(20, 20, 20, 245))
    lw = 520
    lg = LOGO_IM.resize((lw * S, int(LOGO_IM.height * lw / LOGO_IM.width) * S), Image.LANCZOS)
    card.alpha_composite(lg, ((W * S - lg.width) // 2, (cy0 + 60 + dy) * S))
    yl = cy0 + 60 + lg.height // S + 40 + dy
    line(cd, [(cx0 + 60, yl), (cx1 - 60, yl)], ROSA, 2)
    line(cd, [(cx0 + 60, cy1 - 50 + dy), (cx1 - 60, cy1 - 50 + dy)], ROSA, 2)
    text_parts(cd, cy0 + 315 + dy, [("Visite ", False), ("nossa loja", True)], 78)
    f = font("mont", 36)
    cd.text((540 * S, (cy0 + 410 + dy) * S), "Seg a Sex · 13h30 às 17h30", font=f, fill=(235, 230, 228, 255), anchor="mm")
    cd.text((540 * S, (cy0 + 465 + dy) * S), "Cristalina – GO", font=f, fill=(190, 180, 178, 255), anchor="mm")
    cd.text((540 * S, (cy1 - 105 + dy) * S), "@flordelotusvestidos", font=font("mont7", 34), fill=ROSA + (255,), anchor="mm")
    for im in (shadow, card):
        if p < 1:
            im.putalpha(im.split()[3].point(lambda v: int(v * p)))
        base.alpha_composite(im)


# ---------------------------------------------------------------- quadro

VEST_ITEMS = [("barra", 5.0, "Barra"), ("alca", 6.4, "Alça"), ("cintura", 7.8, "Cintura")]
TERNO_ITEMS = [("punho", 12.3, "Punho"), ("barra_calca", 13.7, "Barra da calça"), ("pinca", 15.1, "Pinça na cintura")]
ROWS_Y = [1335, 1420, 1505]


def frame(i):
    t = i / FPS
    base, d = layer()
    gl, gd = layer()

    hk = scene_hook(d, t)
    if hk:
        base.alpha_composite(hk[0])

    # vestido
    if 3.2 <= t <= 10.4:
        title_block(d, t, 3.25, 10.0, "COMO FUNCIONAM OS AJUSTES", [("No ", False), ("vestido", True)])
        draw_garment(d, gd, t, VESTIDO, 3.3, [(n, ti) for n, ti, _ in VEST_ITEMS], 10.0, 0)
        a_out = 1 - ease(prog(t, 10.0, 0.3))
        for (n, ti, lab), y in zip(VEST_ITEMS, ROWS_Y):
            check_row(d, t, ti, y, lab, a_out)
            if n == "cintura" and t >= ti:
                for a, b in SETAS_VESTIDO:
                    arrow(d, tf([a])[0], tf([b])[0], ROSA, a_out, ease(prog(t, ti + 0.1, 0.3)))
    # terno
    if 10.25 <= t <= 17.4:
        title_block(d, t, 10.3, 17.0, "COMO FUNCIONAM OS AJUSTES", [("No ", False), ("terno", True)])
        draw_garment(d, gd, t, TERNO, 10.3, [(n, ti) for n, ti, _ in TERNO_ITEMS], 17.0, 0)
        a_out = 1 - ease(prog(t, 17.0, 0.3))
        pb = ease(prog(t, 11.2, 0.3))
        for bx, by in BOTOES:
            (x, y), = tf([(bx, by)])
            r = 5 * S
            d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), outline=BRANCO + (int(230 * pb * a_out),), width=int(2.4 * S))
        for (n, ti, lab), y in zip(TERNO_ITEMS, ROWS_Y):
            check_row(d, t, ti, y, lab, a_out)
            if n == "pinca" and t >= ti:
                for a, b in SETAS_TERNO:
                    arrow(d, tf([a])[0], tf([b])[0], ROSA, a_out, ease(prog(t, ti + 0.1, 0.3)))

    scene_stamp(d, base, t)
    scene_count(d, t)

    # junta: fundo + brilho + desenho
    small = base.resize((W, H), Image.LANCZOS)
    glow = gl.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(12))
    glow.putalpha(glow.split()[3].point(lambda v: int(v * 0.55)))
    out = BG.copy()
    out.alpha_composite(glow)
    out.alpha_composite(small)

    if t >= 25.1:
        fin, _ = layer()
        scene_final(fin, t)
        out.alpha_composite(fin.resize((W, H), Image.LANCZOS))
    return out.convert("RGB").tobytes()


def init():
    global BG, LOGO_IM
    BG = make_bg()
    LOGO_IM = Image.open(LOGO).convert("RGBA")


def main():
    out = sys.argv[1]
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else DUR
    first = int(float(sys.argv[3]) * FPS) if len(sys.argv) > 3 else 0
    n = int(dur * FPS)
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    with Pool(4, initializer=init) as pool:
        for buf in pool.imap(frame, range(first, n), chunksize=4):
            ff.stdin.write(buf)
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    main()
