"""Demo de motion graphics (tudo se mexendo) para stories 1080x1920@30.
Uso: python3 tools/motion_demo.py | ffmpeg -f rawvideo -pix_fmt bgra -s 1080x1920 -r 30 -i - ... saida.mp4
     python3 tools/motion_demo.py --preview DIR 1.0 4.2 ...   (salva PNGs nesses tempos)
Requer: pip install pycairo"""
import sys, math, random, os
import cairo

W, H, FPS, DUR = 1080, 1920, 30, 11.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "assets", "logo_bblips_mask.png")

# ---------- paleta (a mesma rosa dos vídeos ilustrados) ----------
def rgb(r, g, b): return (r / 255, g / 255, b / 255)
BG1, BG2 = rgb(248, 236, 231), rgb(236, 204, 201)
INK, ROSE, SOFT, BLUSH = rgb(58, 36, 48), rgb(140, 74, 94), rgb(110, 80, 92), rgb(239, 211, 210)
WHITE = (1, 1, 1)

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a))
def out_cubic(x): return 1 - (1 - x) ** 3
def in_out_cubic(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def out_back(x, s=1.70158): x -= 1; return 1 + (s + 1) * x ** 3 + s * x ** 2
def out_elastic(x):
    if x in (0, 1): return x
    return 2 ** (-10 * x) * math.sin((x * 10 - .75) * 2 * math.pi / 3) + 1
def lerp(a, b, k): return a + (b - a) * k

# ---------- utilidades de desenho ----------
def font(c, size, bold=True, serif=False, italic=False):
    c.select_font_face("Liberation Serif" if serif else "Inter",
                       cairo.FONT_SLANT_ITALIC if italic else cairo.FONT_SLANT_NORMAL,
                       cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
    c.set_font_size(size)

def text_w(c, s): return c.text_extents(s).x_advance

def rounded(c, x, y, w, h, r):
    c.new_sub_path()
    c.arc(x + w - r, y + r, r, -math.pi / 2, 0); c.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    c.arc(x + r, y + h - r, r, math.pi / 2, math.pi); c.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    c.close_path()

def path_length(c):
    L, last, start = 0.0, None, None
    for kind, pts in c.copy_path_flat():
        if kind == cairo.PATH_MOVE_TO: last = start = pts
        elif kind == cairo.PATH_LINE_TO: L += math.dist(last, pts); last = pts
        elif kind == cairo.PATH_CLOSE_PATH and last: L += math.dist(last, start); last = start
    return L

def stroke_on(c, k, width, color, alpha=1.0):
    """Desenha o caminho atual 'se fazendo' (k de 0 a 1)."""
    if k <= 0: c.new_path(); return
    L = path_length(c)
    c.set_line_width(width); c.set_line_cap(cairo.LINE_CAP_ROUND); c.set_line_join(cairo.LINE_JOIN_ROUND)
    c.set_source_rgba(*color, alpha); c.set_dash([max(L * k, 0.01), L + 10]); c.stroke(); c.set_dash([])

def sparkle(c, x, y, r, rot, color, alpha):
    c.save(); c.translate(x, y); c.rotate(rot); c.move_to(0, -r)
    for i in range(4):
        a1 = (i + .5) * math.pi / 2 - math.pi / 2; a2 = (i + 1) * math.pi / 2 - math.pi / 2
        c.line_to(math.cos(a1) * r * .22, math.sin(a1) * r * .22); c.line_to(math.cos(a2) * r, math.sin(a2) * r)
    c.close_path(); c.set_source_rgba(*color, alpha); c.fill(); c.restore()

def lips_path(c):
    """Boca centrada em (0,0), ~560 px de largura."""
    c.move_to(-280, 0)
    c.curve_to(-200, -55, -120, -125, -45, -100); c.curve_to(-22, -92, -8, -74, 0, -70)
    c.curve_to(8, -74, 22, -92, 45, -100); c.curve_to(120, -125, 200, -55, 280, 0)
    c.curve_to(190, 135, -190, 135, -280, 0); c.close_path()

def lips_line(c):
    c.move_to(-280, 0); c.curve_to(-150, 22, 150, 22, 280, 0)

# ---------- cenas ----------
def background(c, t):
    g = cairo.LinearGradient(0, 0, 0, H); g.add_color_stop_rgb(0, *BG1); g.add_color_stop_rgb(1, *BG2)
    c.set_source(g); c.paint()
    # bolhas suaves flutuando
    for i, (bx, by, br, sp) in enumerate([(200, 400, 380, .35), (900, 700, 420, .27), (300, 1500, 460, .31), (850, 1700, 360, .4)]):
        x = bx + math.sin(t * sp * 2 + i) * 90; y = by + math.cos(t * sp * 1.6 + i * 2) * 110
        rg = cairo.RadialGradient(x, y, 0, x, y, br)
        rg.add_color_stop_rgba(0, *(BLUSH if i % 2 else WHITE), .55); rg.add_color_stop_rgba(1, *BLUSH, 0)
        c.set_source(rg); c.arc(x, y, br, 0, 2 * math.pi); c.fill()
    # partículas subindo
    rnd = random.Random(3)
    for _ in range(26):
        x0, sp, ph, r = rnd.uniform(0, W), rnd.uniform(40, 110), rnd.uniform(0, H), rnd.uniform(3, 8)
        y = H + 40 - ((t * sp + ph) % (H + 80)); x = x0 + math.sin(t + ph) * 25
        c.set_source_rgba(*WHITE, .55); c.arc(x, y, r, 0, 2 * math.pi); c.fill()

def scene_intro(c, t):
    """0–3.4 s: letras do BBLips caindo com quique, sublinhado se desenhando."""
    word = "BBLips"; font(c, 190, serif=True, bold=True)
    total = text_w(c, word); x = W / 2 - total / 2; y = 960
    out = out_cubic(prog(t, 2.9, 3.4))
    c.save(); c.translate(W / 2, y); c.scale(1 + out * .15, 1 + out * .15); c.translate(-W / 2, -y)
    for i, ch in enumerate(word):
        k = prog(t, .3 + i * .1, .3 + i * .1 + .7)
        dy = (1 - out_elastic(k)) * -260 if k > 0 else -2000
        c.save(); c.translate(x, y + dy)
        c.set_source_rgba(*INK, clamp(k * 3) * (1 - out)); c.move_to(0, 0); c.show_text(ch); c.restore()
        x += text_w(c, ch)
    # sublinhado
    c.new_path(); c.move_to(W / 2 - total / 2, y + 50); c.curve_to(W / 2 - 100, y + 80, W / 2 + 100, y + 30, W / 2 + total / 2, y + 60)
    stroke_on(c, out_cubic(prog(t, 1.2, 2.0)), 10, ROSE, 1 - out)
    # subtítulo deslizando
    k = out_cubic(prog(t, 1.6, 2.3)); font(c, 44, bold=False)
    s = "ESTÉTICA AVANZADA"; c.set_source_rgba(*SOFT, k * (1 - out))
    c.move_to(W / 2 - text_w(c, s) / 2, y + 160 + (1 - k) * 60); c.show_text(s)
    c.restore()

def wipe(c, t, t0, cx, cy, color):
    """Círculo que cresce e cobre a tela (transição)."""
    k = in_out_cubic(prog(t, t0, t0 + .6)); back = in_out_cubic(prog(t, t0 + .6, t0 + 1.2))
    if k <= 0 or back >= 1: return
    R = math.hypot(W, H)
    c.set_source_rgb(*color)
    if back <= 0: c.arc(cx, cy, R * k, 0, 2 * math.pi); c.fill()
    else:  # abre um furo no meio revelando a próxima cena
        c.set_fill_rule(cairo.FILL_RULE_EVEN_ODD); c.rectangle(0, 0, W, H); c.arc(cx, cy, R * back, 0, 2 * math.pi)
        c.fill(); c.set_fill_rule(cairo.FILL_RULE_WINDING)

def scene_lips(c, t):
    """3.6–7.2 s: boca se desenhando, enchendo de cor, brilhos e texto palavra a palavra."""
    lt = t - 3.6
    if lt < 0 or t > 7.6: return
    out = in_out_cubic(prog(t, 7.0, 7.5))
    cy = 820 + math.sin(lt * 2) * 8  # leve flutuação
    c.save(); c.translate(W / 2 - out * 1200, cy)
    fill = out_back(prog(lt, 1.0, 1.7)); s = .9 + .1 * fill
    c.save(); c.scale(s, s); lips_path(c)
    g = cairo.LinearGradient(0, -120, 0, 120); g.add_color_stop_rgb(0, .78, .36, .45); g.add_color_stop_rgb(1, .55, .22, .32)
    c.set_source(g); c.save(); c.clip_preserve(); c.paint_with_alpha(clamp(fill)); c.restore()
    stroke_on(c, out_cubic(prog(lt, .1, 1.1)), 8, INK)
    lips_line(c); stroke_on(c, out_cubic(prog(lt, .7, 1.3)), 6, INK)
    # reflexo de brilho passando
    sh = prog(lt, 1.6, 2.4)
    if 0 < sh < 1:
        lips_path(c); c.save(); c.clip()
        x = lerp(-400, 400, sh); lg = cairo.LinearGradient(x - 80, 0, x + 80, 0)
        lg.add_color_stop_rgba(0, 1, 1, 1, 0); lg.add_color_stop_rgba(.5, 1, 1, 1, .5); lg.add_color_stop_rgba(1, 1, 1, 1, 0)
        c.set_source(lg); c.paint(); c.restore()
    c.restore()
    for i, (sx, sy, sr) in enumerate([(-300, -150, 46), (310, -120, 36), (250, 150, 28), (-240, 170, 32), (0, -210, 40)]):
        k = out_back(prog(lt, 1.4 + i * .12, 1.9 + i * .12), 3)
        if k > 0: sparkle(c, sx, sy, sr * k * (1 + .15 * math.sin(lt * 6 + i)), lt * .8 + i, ROSE, .9)
    c.restore()
    # texto palavra por palavra
    font(c, 96, serif=True, italic=True, bold=False)
    words = ["Volumen", "natural,"]; line2 = ["sin", "agujas"]
    for row, ws in enumerate([words, line2]):
        tot = sum(text_w(c, w + " ") for w in ws) - text_w(c, " "); x = W / 2 - tot / 2
        for j, w in enumerate(ws):
            k = out_back(prog(lt, 1.8 + (row * 2 + j) * .18, 2.4 + (row * 2 + j) * .18))
            c.set_source_rgba(*(ROSE if row else INK), clamp(k) * (1 - out))
            c.move_to(x - out * 1200, 1180 + row * 120 + (1 - k) * 70); c.show_text(w); x += text_w(c, w + " ")

def scene_cards(c, t):
    """7.2–11 s: cartões entrando em cascata com check se desenhando + botão pulsando + logo."""
    lt = t - 7.2
    if lt < 0: return
    font(c, 70, serif=True, bold=True); s = "¿Por qué Hyaluron Pen?"
    k = out_cubic(prog(lt, 0, .5)); c.set_source_rgba(*INK, k)
    c.move_to(W / 2 - text_w(c, s) / 2, 560 - (1 - k) * 50); c.show_text(s)
    for i, label in enumerate(["Sin agujas", "Resultado sutil", "Rápido y cómodo"]):
        k = out_back(prog(lt, .25 + i * .2, .95 + i * .2), 1.2)
        if k <= 0: continue
        x = lerp(W + 50, 130, k); y = 660 + i * 190
        c.save(); c.translate(x, y + math.sin(lt * 2.4 + i) * 4)
        c.set_source_rgba(.35, .15, .2, .10); rounded(c, 6, 14, 820, 150, 40); c.fill()  # sombra
        c.set_source_rgb(*WHITE); rounded(c, 0, 0, 820, 150, 40); c.fill()
        c.set_source_rgb(*BLUSH); c.arc(85, 75, 46, 0, 2 * math.pi); c.fill()
        c.new_path(); c.move_to(63, 77); c.line_to(80, 94); c.line_to(110, 58)
        stroke_on(c, out_cubic(prog(lt, .8 + i * .2, 1.2 + i * .2)), 10, ROSE)
        font(c, 54, bold=True); c.set_source_rgb(*INK); c.move_to(160, 94); c.show_text(label)
        c.restore()
    # botão com pulso
    k = out_elastic(prog(lt, 1.5, 2.4))
    if k > 0:
        pulse = 1 + .04 * math.sin(lt * 7) * clamp(lt - 2.2)
        c.save(); c.translate(W / 2, 1360); c.scale(k * pulse, k * pulse)
        ring = (lt * 1.2) % 1
        if lt > 2.2:
            c.set_source_rgba(*ROSE, .35 * (1 - ring)); rounded(c, -330 - ring * 40, -70 - ring * 40, 660 + ring * 80, 140 + ring * 80, 70 + ring * 40); c.fill()
        c.set_source_rgb(*ROSE); rounded(c, -330, -70, 660, 140, 70); c.fill()
        font(c, 52, bold=True); s = "Reserva tu cita"; c.set_source_rgb(*WHITE)
        c.move_to(-text_w(c, s) / 2, 18); c.show_text(s); c.restore()
    # logo girando de leve e entrando
    k = out_back(prog(lt, 2.2, 2.9))
    if k > 0 and LOGO_SURF:
        sc = .42 * k; c.save(); c.translate(W / 2, 1640); c.rotate((1 - k) * -.6); c.scale(sc, sc)
        c.translate(-LOGO_SURF.get_width() / 2, -LOGO_SURF.get_height() / 2)
        c.set_source_rgba(*ROSE, clamp(k)); c.mask_surface(LOGO_SURF); c.restore()  # logo pintado na cor rosa

def fade_edges(c, t):
    a = max(1 - prog(t, 0, .35), prog(t, DUR - .4, DUR))
    if a > 0: c.set_source_rgba(*BG1, a); c.paint()

LOGO_SURF = cairo.ImageSurface.create_from_png(LOGO) if os.path.exists(LOGO) else None

def frame(t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H); c = cairo.Context(surf)
    background(c, t)
    if t < 3.6: scene_intro(c, t)
    scene_lips(c, t)
    if t >= 7.0: scene_cards(c, t)
    wipe(c, t, 3.0, W / 2, 960, ROSE)
    fade_edges(c, t)
    surf.flush(); return surf

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview":
        os.makedirs(sys.argv[2], exist_ok=True)
        for ts in sys.argv[3:]: frame(float(ts)).write_to_png(os.path.join(sys.argv[2], f"t{float(ts):05.2f}.png"))
    else:
        out = sys.stdout.buffer
        for i in range(int(DUR * FPS)): out.write(bytes(frame(i / FPS).get_data()))
