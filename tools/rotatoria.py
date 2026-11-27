"""Vídeo 100% desenhado: Rotatória · quem passa primeiro? (@instrutorgustavovieira)

Uso: python3 rotatoria.py <saida.mp4> [inicio] [fim]
Gera só o vídeo (sem áudio), 1080x1920 a 30 qps, desenhado quadro a quadro com Pillow.
"""
import math, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
SB = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
SBI = "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"
INTER = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"

PAPER = (236, 224, 196); CARD = (244, 235, 212); INK = (34, 30, 28)
YEL = (255, 196, 0); NAVY = (52, 56, 82); RED = (196, 40, 40); GREEN = (58, 164, 92)
ROAD = (66, 68, 84); GRASS = (124, 186, 94); GRASS2 = (100, 162, 76); WHITE = (246, 244, 236)
GCAR = (58, 164, 92); YCAR = (255, 196, 0)

_fonts = {}
def F(path, size):
    k = (path, size)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(path, size)
    return _fonts[k]

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(p): p = clamp(p); return 1 - (1 - p) ** 3
def ease_io(p): p = clamp(p); return 3 * p * p - 2 * p * p * p
def prog(t, a, b): return clamp((t - a) / (b - a)) if b > a else float(t >= a)

rng = np.random.default_rng(7)

# ---------------------------------------------------------------- mapa
MAP_Y0, MAP_H = 420, 1080           # faixa do mapa na tela
CX, CY = 540, 500                   # centro da rotatória (coord. do mapa)
R_ISLAND, R_IN, R_DIV, R_OUT, R_EDGE = 135, 185, 237, 289, 340
ROAD_HALF = 120                     # vias de acesso: 240 px
LANE = 60                           # centro da faixa da direita a partir do eixo

def paper_texture(w, h, base, amt=7):
    a = np.empty((h, w, 3), np.int16); a[:] = base
    n = rng.normal(0, amt, (h, w))[..., None]
    fib = rng.normal(0, 3, (h, 1))[..., None]
    return Image.fromarray(np.clip(a + n + fib, 0, 255).astype(np.uint8))

def build_static_map():
    m = paper_texture(W, MAP_H, GRASS, 6).convert("RGBA")
    d = ImageDraw.Draw(m)
    for _ in range(46):                                   # árvores
        x, y, r = int(rng.integers(0, W)), int(rng.integers(0, MAP_H)), int(rng.integers(26, 52))
        if math.hypot(x - CX, y - CY) < R_EDGE + r + 10: continue
        if abs(x - CX) < ROAD_HALF + r or abs(y - CY) < ROAD_HALF + r: continue
        d.ellipse([x - r, y - r, x + r, y + r], fill=GRASS2)
    # vias de acesso
    d.rectangle([CX - ROAD_HALF, 0, CX + ROAD_HALF, MAP_H], fill=ROAD)
    d.rectangle([0, CY - ROAD_HALF, W, CY + ROAD_HALF], fill=ROAD)
    d.ellipse([CX - R_EDGE, CY - R_EDGE, CX + R_EDGE, CY + R_EDGE], fill=ROAD)
    # faixas amarelas centrais das vias de acesso
    for y in range(0, MAP_H, 80):
        if abs(y - CY) > R_EDGE + 10 and abs(y + 44 - CY) > R_EDGE + 10:
            d.rectangle([CX - 4, y, CX + 4, y + 44], fill=YEL)
    for x in range(0, W, 80):
        if abs(x - CX) > R_EDGE + 10 and abs(x + 44 - CX) > R_EDGE + 10:
            d.rectangle([x, CY - 4, x + 44, CY + 4], fill=YEL)
    # divisor tracejado branco entre as duas faixas do anel
    for k in range(36):
        a0 = k * 10; d.arc([CX - R_DIV, CY - R_DIV, CX + R_DIV, CY + R_DIV], a0, a0 + 5, fill=WHITE, width=5)
    # linhas de "dê a preferência" (tracejadas) nas 4 entradas
    for ang in (90, 0, 270, 180):
        for k in range(5):
            off = 12 + k * 22
            if ang == 90:   d.rectangle([CX + off, CY + R_EDGE + 4, CX + off + 12, CY + R_EDGE + 12], fill=WHITE)
            if ang == 270:  d.rectangle([CX - off - 12, CY - R_EDGE - 12, CX - off, CY - R_EDGE - 4], fill=WHITE)
            if ang == 0:    d.rectangle([CX + R_EDGE + 4, CY - off - 12, CX + R_EDGE + 12, CY - off], fill=WHITE)
            if ang == 180:  d.rectangle([CX - R_EDGE - 12, CY + off, CX - R_EDGE - 4, CY + off + 12], fill=WHITE)
    # ilha central
    d.ellipse([CX - R_ISLAND, CY - R_ISLAND, CX + R_ISLAND, CY + R_ISLAND], fill=GRASS, outline=WHITE, width=8)
    for (dx, dy, r) in [(-30, -20, 48), (38, 22, 40), (-12, 44, 30)]:
        d.ellipse([CX + dx - r, CY + dy - r, CX + dx + r, CY + dy + r], fill=GRASS2)
    return m

# ---------------------------------------------------------------- carros e caminhos
def car_sprite(color, stripe=None):
    w, h = 96, 168
    s = Image.new("RGBA", (w + 24, h + 24), (0, 0, 0, 0))
    sh = Image.new("RGBA", s.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([14, 18, 14 + w, 18 + h], 28, fill=(0, 0, 0, 90))
    s.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(s); x, y = 12, 12
    d.rounded_rectangle([x, y, x + w, y + h], 28, fill=color, outline=(30, 30, 30), width=3)
    d.rounded_rectangle([x + 14, y + 26, x + w - 14, y + 62], 10, fill=(40, 44, 60))   # para-brisa (frente = cima)
    d.rounded_rectangle([x + 16, y + 118, x + w - 16, y + 144], 9, fill=(40, 44, 60))
    if stripe: d.rectangle([x + 3, y + 78, x + w - 3, y + 100], fill=stripe)
    return s

SPR = {"g": car_sprite(GCAR), "y": car_sprite(YCAR, WHITE)}

def blinker_sprite(sprite, on):
    s = sprite.copy()
    if on:
        d = ImageDraw.Draw(s)
        for (x, y) in [(104, 22), (104, 176)]:   # lado direito, frente e trás
            d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=(255, 140, 0), outline=(255, 230, 160), width=3)
    return s

def ring_pt(r, theta_deg):
    a = math.radians(theta_deg)
    return (CX + r * math.cos(a), CY - r * math.sin(a))

def bezier(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out

def arc(r, a0, a1, step=2):
    n = max(2, int(abs(a1 - a0) / step))
    return [ring_pt(r, a0 + (a1 - a0) * i / n) for i in range(n + 1)]

class Path:
    def __init__(self, pts):
        self.p = np.array(pts, float)
        seg = np.hypot(*np.diff(self.p, axis=0).T); self.cum = np.concatenate([[0], np.cumsum(seg)]); self.L = self.cum[-1]
    def at(self, s):                     # s em [0,1] por comprimento
        d = clamp(s) * self.L
        i = int(np.searchsorted(self.cum, d)); i = min(max(i, 1), len(self.p) - 1)
        a, b = self.p[i - 1], self.p[i]; f = (d - self.cum[i - 1]) / max(1e-6, self.cum[i] - self.cum[i - 1])
        x, y = a + (b - a) * f; dx, dy = b - a
        ang = math.degrees(math.atan2(-dy, dx)) - 90       # rotação do sprite (frente = cima)
        return x, y, ang
    def upto(self, s):
        d = clamp(s) * self.L; i = int(np.searchsorted(self.cum, d))
        return [tuple(q) for q in self.p[:max(i, 1)]] + [self.at(s)[:2]]

STOP_Y = CY + R_EDGE + 100           # onde o carro amarelo para, antes da linha
ENTRY_X = CX + LANE

def entry_path(r_lane, exit_theta=None, start_y=MAP_H + 120, extra_ring=None):
    """Sobe pela faixa da direita da via sul, entra na rotatória (sentido anti-horário) na faixa r_lane."""
    j = -62 if r_lane == R_OUT else -55
    p_join = ring_pt(r_lane, j)
    a = math.radians(j); tang = (-math.sin(a), -math.cos(a))
    pts = [(ENTRY_X, start_y), (ENTRY_X, STOP_Y)]
    pts += bezier((ENTRY_X, STOP_Y), (ENTRY_X, STOP_Y - 90),
                  (p_join[0] - tang[0] * 90, p_join[1] - tang[1] * 90), p_join)[1:]
    end = exit_theta if exit_theta is not None else (extra_ring if extra_ring else 120)
    pts += arc(r_lane, j, end)[1:]
    if exit_theta is not None:
        pts += exit_east_tail(r_lane, end)
    return Path(pts)

def exit_east_tail(r_lane, theta):
    p = ring_pt(r_lane, theta); a = math.radians(theta); tang = (-math.sin(a), -math.cos(a))
    q = (CX + R_EDGE + 60, CY + LANE)
    return bezier(p, (p[0] + tang[0] * 80, p[1] + tang[1] * 80), (q[0] - 90, q[1]), q)[1:] + [(W + 140, CY + LANE)]

def frac_of(path, y_target):
    """fração de comprimento em que o caminho chega a y_target subindo pela entrada."""
    d = path.p[0][1] - y_target
    return d / path.L

# ---------------------------------------------------------------- elementos de texto
def tag_img(text, size, bg, fg, rot, font=SB, pad=(26, 14), hi=None, hi_color=YEL):
    """Etiqueta torta estilo papel. hi = palavra que recebe destaque (fundo amarelo)."""
    f = F(font, size); tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    l, t, r, b = tmp.textbbox((0, 0), text, font=f); w, h = r - l + 2 * pad[0], b - t + 2 * pad[1]
    L = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rectangle([30, 30, 30 + w, 30 + h], fill=bg)
    if hi and hi in text:
        pre = text[: text.index(hi)]; x0 = 30 + pad[0] - l + tmp.textlength(pre, font=f); x1 = x0 + tmp.textlength(hi, font=f)
        d.rectangle([x0 - 8, 30 + 6, x1 + 8, 30 + h - 6], fill=hi_color)
    d.text((30 + pad[0] - l, 30 + pad[1] - t), text, font=f, fill=fg)
    L = L.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 85), (0, 0), L.split()[3])
    out = Image.new("RGBA", (L.width + 20, L.height + 20), (0, 0, 0, 0))
    out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)), (6, 10)); out.alpha_composite(L, (0, 0))
    return out

_tag_cache = {}
def tag(text, size, bg, fg, rot, **kw):
    k = (text, size, bg, fg, rot, tuple(sorted(kw.items())))
    if k not in _tag_cache: _tag_cache[k] = tag_img(text, size, bg, fg, rot, **kw)
    return _tag_cache[k]

def paste_scaled(canvas, img, center, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01: return
    im = img
    if abs(scale - 1) > 0.005:
        im = img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.BICUBIC)
    if alpha < 0.999:
        im = im.copy(); a = im.split()[3].point(lambda v: int(v * alpha)); im.putalpha(a)
    canvas.alpha_composite(im, (int(center[0] - im.width / 2), int(center[1] - im.height / 2)))

def pop(t, t0, dur=0.3):
    """entrada com passada do ponto: 0.6 -> 1.08 -> 1.0"""
    p = prog(t, t0, t0 + dur)
    if p <= 0: return 0.0
    if p < 0.65: return 0.6 + 0.48 * ease_out(p / 0.65)
    return 1.08 - 0.08 * ease_io((p - 0.65) / 0.35)

def slide_in(t, t0, t_out=None, dur=0.3, out_dur=0.2):
    """retorna (alpha, deslocamento) para entrada deslizando + saída com fade"""
    a = ease_out(prog(t, t0, t0 + dur)); dy = (1 - a) * 40
    if t_out is not None: a *= 1 - prog(t, t_out, t_out + out_dur)
    return a, dy

def stamp(t, t0):
    """carimbo: 1.6 -> 0.95 -> 1.0 em 0.18 s + tremor"""
    p = prog(t, t0, t0 + 0.18)
    if t < t0: return 0.0, 0
    if p < 1: return 1.6 - 0.65 * ease_out(p), 0
    q = prog(t, t0 + 0.18, t0 + 0.26)
    shake = 3 if t < t0 + 0.3 else 0
    return 0.95 + 0.05 * q, shake

def stamp_img(text, color, size=120, rot=-8):
    f = F(SB, size); tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    l, t, r, b = tmp.textbbox((0, 0), text, font=f); w, h = r - l + 70, b - t + 50
    L = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    d.rectangle([20, 20, 20 + w, 20 + h], outline=color + (255,), width=12)
    d.text((20 + 35 - l, 20 + 25 - t), text, font=f, fill=color + (255,))
    a = np.array(L); m = rng.random(a.shape[:2]) < 0.10; a[..., 3][m] = (a[..., 3][m] * 0.4).astype(np.uint8)   # textura de tinta
    return Image.fromarray(a).rotate(rot, expand=True, resample=Image.BICUBIC)

STAMPS = {"ESPERA": stamp_img("ESPERA", RED), "SETA!": stamp_img("SETA!", (232, 120, 20))}

# placas
def sign_pare(sz=150):
    s = Image.new("RGBA", (sz, sz + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(s); R = sz / 2 - 6; c = sz / 2
    d.rectangle([c - 7, c, c + 7, sz + 118], fill=(150, 150, 160))
    pts = [(c + R * math.cos(math.radians(22.5 + 45 * i)), c + R * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
    d.polygon(pts, fill=RED, outline=WHITE, width=7)
    f = F(SB, int(sz * 0.27)); w = d.textlength("PARE", font=f); d.text((c - w / 2, c - sz * 0.16), "PARE", font=f, fill=WHITE)
    return s

def sign_yield(sz=160):
    s = Image.new("RGBA", (sz, sz + 110), (0, 0, 0, 0)); d = ImageDraw.Draw(s); c = sz / 2
    d.rectangle([c - 7, sz * 0.7, c + 7, sz + 108], fill=(150, 150, 160))
    d.polygon([(6, 10), (sz - 6, 10), (c, sz * 0.86)], fill=RED)
    d.polygon([(30, 26), (sz - 30, 26), (c, sz * 0.86 - 34)], fill=WHITE)
    return s

SIGNS = {"pare": sign_pare(), "yield": sign_yield()}
SIGN_POS = (CX + ROAD_HALF + 95, STOP_Y - 40)     # gramado à direita da entrada sul

# ---------------------------------------------------------------- linha do tempo (segundos do áudio cortado)
T_GANCHO = 0.0
T_PREF, T_ESPERA_IN, T_ESPERA = 3.92, 7.05, 8.53
T_ATENCAO, T_PLACA = 9.20, 10.05
T_PARE, T_RODAS, T_OLHA, T_LIVRE = 13.43, 15.9, 17.47, 19.0
T_YIELD, T_REDUZ, T_DEIXA = 19.95, 21.69, 22.75
T_ENTROU, T_DIR, T_ESQ = 25.91, 26.46, 29.02
T_SAIR, T_SETA, T_INFRA = 31.27, 32.35, 34.93
T_RESUMO, T_R1, T_R2, T_R3 = 37.05, 37.78, 38.98, 40.35
T_FINAL, T_END = 41.83, 43.84

# caminhos fixos
GREEN_RING_A = Path(arc(R_OUT, 200, 200 + 360 * 3))       # verdes girando no anel (anti-horário)
P_ESPERA = entry_path(R_OUT, exit_theta=-25)
P_PARE = entry_path(R_OUT, exit_theta=-25)
P_YIELD = entry_path(R_OUT, exit_theta=-25)
P_DIR = entry_path(R_OUT, exit_theta=-25, start_y=STOP_Y + 1)
P_ESQ = entry_path(R_IN, start_y=STOP_Y + 1, extra_ring=170)
P_SETA = Path(arc(R_OUT, -190, -25) + exit_east_tail(R_OUT, -25))
F_STOP = frac_of(P_PARE, STOP_Y)

def ring_car_at(theta_deg, r=R_OUT):
    x, y = ring_pt(r, theta_deg); return x, y, theta_deg

def draw_car(m, spr, x, y, ang):
    im = spr.rotate(ang, expand=True, resample=Image.BICUBIC)
    m.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))

def drive(t, t0, t1, s0, s1, mode="io"):
    p = prog(t, t0, t1)
    e = ease_io(p) if mode == "io" else (ease_out(p) if mode == "out" else (p * p if mode == "in" else p))
    return s0 + (s1 - s0) * e

def green_cars(t, phase_deg=0, speed=48):
    """posições dos carros verdes que circulam (graus por segundo)."""
    return [(200 + phase_deg + speed * t + off) for off in (0, 150)]

def dashed_poly(d, pts, color, width=8, dash=22, gap=16):
    acc, on = 0.0, True; seglen = dash
    for i in range(1, len(pts)):
        (x0, y0), (x1, y1) = pts[i - 1], pts[i]; L = math.hypot(x1 - x0, y1 - y0); pos = 0
        while pos < L:
            step = min(seglen - acc, L - pos); a = pos / L; b = (pos + step) / L
            if on: d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], fill=color, width=width)
            pos += step; acc += step
            if acc >= seglen - 1e-6: acc = 0; on = not on; seglen = dash if on else gap

# ---------------------------------------------------------------- quadro
STATIC_MAP = build_static_map()
PAPER_BG = paper_texture(W, H, PAPER, 6).convert("RGBA")

def map_layer(t):
    m = STATIC_MAP.copy(); d = ImageDraw.Draw(m)
    G, Y = SPR["g"], SPR["y"]

    # --- placas
    sign, s_scale = None, 0
    if T_PLACA <= t < T_YIELD: sign, s_scale = "pare", pop(t, T_PLACA + 0.3, 0.3)
    elif T_YIELD <= t < T_ENTROU: sign, s_scale = "yield", pop(t, T_YIELD, 0.3)
    if sign and s_scale > 0:
        paste_scaled(m, SIGNS[sign], SIGN_POS, s_scale)

    # --- cena por cena
    if t < T_ESPERA_IN:                                              # gancho + preferência: só verdes girando
        for th in green_cars(t): draw_car(m, G, *ring_car_at(th))
        if t >= T_PREF:                                              # anel de destaque no verde líder
            x, y, _ = ring_car_at(green_cars(t)[0]); p = ease_out(prog(t, T_PREF, T_PREF + 0.4))
            r = 100 + 20 * (1 - p); d.ellipse([x - r, y - r, x + r, y + r], outline=YEL + (int(255 * p),), width=8)
    elif t < T_PLACA:                                                # "você, que vai entrar, espera"
        s = drive(t, T_ESPERA_IN, T_ESPERA_IN + 1.4, 0, F_STOP, "out")
        draw_car(m, Y, *P_ESPERA.at(s))
        for th in green_cars(t): draw_car(m, G, *ring_car_at(th))
    elif t < T_YIELD:                                                # PARE
        if t < T_PARE: s = F_STOP
        elif t < T_LIVRE: s = F_STOP                                 # já parado na linha (vem da cena anterior)
        else: s = drive(t, T_LIVRE, T_YIELD + 0.2, F_STOP, 0.55, "in")
        draw_car(m, Y, *P_PARE.at(s))
        # verde passa pela frente enquanto ele está parado
        th = drive(t, T_OLHA - 0.6, T_LIVRE - 0.1, 190, 330, "lin") if t >= T_OLHA - 0.6 else 190
        if t < T_LIVRE + 0.6: draw_car(m, G, *ring_car_at(th))
        if T_RODAS <= t < T_LIVRE:                                   # marcas de "travado" nas rodas
            x, y, _ = P_PARE.at(F_STOP); a = int(255 * ease_out(prog(t, T_RODAS, T_RODAS + 0.3)))
            for dx in (-62, 62):
                for dy in (-50, 50): d.line([(x + dx - 10, y + dy), (x + dx + 10, y + dy)], fill=RED + (a,), width=6)
        if T_OLHA <= t < T_LIVRE:                                    # olhar para a esquerda (cone tracejado)
            x, y, _ = P_PARE.at(F_STOP); p = ease_out(prog(t, T_OLHA, T_OLHA + 0.4))
            ov = Image.new("RGBA", m.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            tip = (x - 40 - 300 * p, y - 120 - 140 * p)
            od.polygon([(x - 20, y - 70), tip, (tip[0] + 40, tip[1] + 150)], fill=(255, 255, 255, 70))
            m.alpha_composite(ov)
    elif t < T_ENTROU:                                               # DÊ A PREFERÊNCIA
        if t < T_REDUZ: s = drive(t, T_YIELD, T_REDUZ, 0, F_STOP * 0.82, "lin")
        elif t < T_DEIXA + 1.2: s = drive(t, T_REDUZ, T_DEIXA + 1.2, F_STOP * 0.82, F_STOP, "out")
        else: s = drive(t, T_DEIXA + 1.2, T_ENTROU + 0.3, F_STOP, 0.55, "in")
        draw_car(m, Y, *P_YIELD.at(s))
        th = drive(t, T_DEIXA - 0.6, T_DEIXA + 1.6, 175, 340, "lin") if t >= T_DEIXA - 0.6 else 175
        draw_car(m, G, *ring_car_at(th))
    elif t < T_SAIR:                                                 # duas faixas
        # trilhas tracejadas
        p1 = drive(t, T_DIR, T_DIR + 2.0, 0, 1, "io"); p2 = drive(t, T_ESQ, T_ESQ + 2.0, 0, 1, "io")
        if t >= T_DIR: dashed_poly(d, P_DIR.upto(min(p1, 0.85)), YEL + (230,), 8)
        if t >= T_ESQ: dashed_poly(d, P_ESQ.upto(min(p2, 0.93)), WHITE + (230,), 8)
        draw_car(m, Y, *P_DIR.at(p1 if t >= T_DIR else 0))
        if t >= T_ESQ - 0.4: draw_car(m, G, *P_ESQ.at(p2))
    elif t < T_RESUMO:                                               # seta para sair
        s = drive(t, T_SAIR, T_INFRA - 0.2, 0, 1, "io")
        blink = t >= T_SAIR + 0.5 and int((t - T_SAIR) * 2.5) % 2 == 0
        draw_car(m, blinker_sprite(Y, blink), *P_SETA.at(s))
        for th in green_cars(t, 60): draw_car(m, G, *ring_car_at(th, R_IN))
    else:                                                            # resumo e final: mapa calmo ao fundo
        for th in green_cars(t): draw_car(m, G, *ring_car_at(th))
    return m

def zoom_for(t):
    """zoom na entrada sul durante as cenas das placas."""
    zin = ease_io(prog(t, T_ATENCAO, T_ATENCAO + 0.8)); zout = ease_io(prog(t, T_ENTROU - 0.2, T_ENTROU + 0.5))
    k = zin * (1 - zout)
    return 1 + 0.32 * k, (CX + 60 * k, CY + 330 * k)

def top_card(c):
    d = ImageDraw.Draw(c)
    d.rectangle([40, 250, 1040, 386], fill=CARD); d.rectangle([40, 382, 1040, 386], fill=(210, 196, 166))
    f = F(SB, 44); t = "ROTATÓRIA · QUEM PASSA PRIMEIRO?"; d.text(((W - d.textlength(t, font=f)) / 2, 266), t, font=f, fill=INK)
    fs = F(SB, 28)
    for x0, txt, col in [(300, "já está dentro", GREEN), (580, "vai entrar", (226, 168, 0))]:
        w = d.textlength(txt, font=fs) + 44
        d.rounded_rectangle([x0, 328, x0 + w, 370], 20, fill=col); d.text((x0 + 22, 332), txt, font=fs, fill=WHITE)

HANDLE = "@INSTRUTORGUSTAVOVIEIRA"

def overlay_tags(c, t):
    """etiquetas e carimbos sobre a tela (coordenadas de tela)."""
    # gancho
    if t < T_PREF:
        a1 = pop(t, 0.08, 0.25); a2 = pop(t, 1.04, 0.25)
        fade = 1 - prog(t, T_PREF - 0.25, T_PREF)
        paste_scaled(c, tag("Na rotatória,", 76, WHITE, INK, 2), (540, 520), a1, fade)
        paste_scaled(c, tag("quem passa primeiro?", 84, NAVY, WHITE, -2, hi="passa", hi_color=(255, 196, 0)), (540, 640), a2, fade)
    def lower(text, t0, t1, bg, fg=WHITE, rot=-2, y=1565, size=64, **kw):
        if t0 <= t < t1 + 0.2:
            a, dy = slide_in(t, t0, t1)
            paste_scaled(c, tag(text, size, bg, fg, rot, **kw), (540, y + dy), 1, a)
    lower("quem já está dentro tem a preferência", T_PREF + 0.3, T_ESPERA_IN, GREEN, size=56)
    lower("você, que vai entrar…", T_ESPERA_IN, T_ATENCAO, (226, 168, 0), INK, 2)
    lower("mas atenção:", T_ATENCAO, T_PLACA, NAVY)
    lower("vale o que a placa manda", T_PLACA, T_PARE, NAVY, rot=2)
    lower("PARE: para totalmente", T_PARE, T_RODAS, RED)
    lower("rodas 100% paradas", T_RODAS, T_OLHA, RED, rot=2)
    lower("olha à esquerda e entra quando estiver livre", T_OLHA, T_YIELD - 0.1, NAVY, size=48)
    lower("DÊ A PREFERÊNCIA: reduz", T_YIELD, T_DEIXA, RED, size=58)
    lower("e deixa passar quem já está dentro", T_DEIXA, T_ENTROU, GREEN, rot=2, size=54)
    lower("entrou?", T_ENTROU, T_DIR, NAVY, y=1560)
    lower("faixa da DIREITA: sai logo", T_DIR, T_RESUMO - 6.0, (226, 168, 0), INK, y=1560, size=58)
    lower("faixa da ESQUERDA: volta maior", T_ESQ, T_SAIR, NAVY, rot=2, y=1650, size=58)
    lower("seta para a direita antes de sair", T_SAIR, T_INFRA, (226, 168, 0), INK, size=56)
    lower("sem seta = infração", T_INFRA, T_RESUMO, RED, rot=2, size=72)
    # carimbos
    for key, t0, t1, pos in [("ESPERA", T_ESPERA, T_ATENCAO, (290, 1150)), ("SETA!", T_SETA, T_INFRA, (300, 650))]:
        if t0 <= t < t1:
            sc, sh = stamp(t, t0); fade = 1 - prog(t, t1 - 0.2, t1)
            off = (sh if int(t * 30) % 2 else -sh)
            paste_scaled(c, STAMPS[key], (pos[0] + off, pos[1]), sc, fade)

def summary_card(c, t):
    if t < T_RESUMO: return
    a = ease_out(prog(t, T_RESUMO, T_RESUMO + 0.3))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.rectangle([0, 0, W, H], fill=PAPER + (int(225 * a),))
    c.alpha_composite(ov)
    if t < T_FINAL:
        paste_scaled(c, tag("resumindo:", 70, NAVY, WHITE, -2), (540, 660 + (1 - a) * 40), 1, a)
        items = [("respeita a placa", T_R1), ("quem está dentro passa", T_R2), ("dá seta pra sair", T_R3)]
        for i, (txt, t0) in enumerate(items):
            if t < t0: continue
            p = ease_out(prog(t, t0, t0 + 0.2)); y = 840 + i * 190; x = 150 - (1 - p) * 40
            box = Image.new("RGBA", (860, 150), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
            bd.rectangle([0, 0, 859, 149], fill=CARD); bd.rectangle([0, 146, 859, 149], fill=(210, 196, 166))
            cp = ease_out(prog(t, t0 + 0.05, t0 + 0.25))
            bd.ellipse([30, 30, 120, 120], outline=GREEN, width=8) if cp >= 1 else bd.arc([30, 30, 120, 120], -90, -90 + 360 * cp, fill=GREEN, width=8)
            if cp > 0.5: bd.line([(52, 76), (70, 96), (100, 56)], fill=GREEN, width=10, joint="curve")
            bd.text((150, 44), txt, font=F(SB, 58), fill=INK)
            al = box.split()[3].point(lambda v: int(v * p)); box.putalpha(al)
            c.alpha_composite(box, (int(x), y))
    else:
        p = pop(t, T_FINAL, 0.3)
        paste_scaled(c, tag("Me segue para mais", 74, NAVY, WHITE, -2), (540, 880), p)
        paste_scaled(c, tag("dicas de trânsito", 92, YEL, INK, 2), (540, 1020), pop(t, T_FINAL + 0.35, 0.3))
        q = ease_out(prog(t, T_FINAL + 0.7, T_FINAL + 1.0))
        if q > 0:
            box = tag("@instrutorgustavovieira", 52, WHITE, INK, 0, font=INTER)
            paste_scaled(c, box, (540, 1200 + (1 - q) * 30), 1, q)

def frame(t):
    c = PAPER_BG.copy()
    m = map_layer(t)
    z, (fx, fy) = zoom_for(t)
    if z > 1.001:
        cw, ch = W / z, MAP_H / z
        x0 = clamp(fx - cw / 2, 0, W - cw); y0 = clamp(fy - ch / 2, 0, MAP_H - ch)
        m = m.resize((W, MAP_H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    c.alpha_composite(m, (0, MAP_Y0))
    ImageDraw.Draw(c).rectangle([0, MAP_Y0 + MAP_H - 4, W, MAP_Y0 + MAP_H], fill=(205, 190, 160))
    top_card(c)
    overlay_tags(c, t)
    summary_card(c, t)
    d = ImageDraw.Draw(c); f = F(SB, 26)
    d.text((40, MAP_Y0 + MAP_H - 50), HANDLE, font=f, fill=(245, 245, 235))
    return c.convert("RGB")

def main():
    out = sys.argv[1]; t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0; t1 = float(sys.argv[3]) if len(sys.argv) > 3 else T_END
    if len(sys.argv) > 4:                       # modo quadros: salva PNGs nos tempos dados
        for tt in sys.argv[4].split(","): frame(float(tt)).save(f"{out}_{float(tt):05.2f}.png")
        return
    n = int(round((t1 - t0) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                          "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", out], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(frame(t0 + i / FPS).tobytes())
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    main()
