"""Cruzamento sem placa e sem semáforo: quem passa primeiro? (quiz A/B, ~1min17, tela cheia)
Uso: python3 cruzamento.py <saida.mp4> [inicio] [fim] [t1,t2,... => PNGs]
"""
import math, subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from rotatoria import (W, H, FPS, F, SB, INTER, PAPER, CARD, INK, YEL, NAVY, RED, GREEN, WHITE, ROAD, GRASS, GRASS2,
                       paper_texture, car_sprite, tag, paste_scaled, pop, slide_in, stamp, stamp_img, draw_car, drive,
                       clamp, prog, ease_out, ease_io, Path, bezier, blinker_sprite)

ORANGE = (226, 168, 0)
CX, CY = 540, 900
WH, NH = 170, 110                 # meia largura: rua larga (horizontal) e estreita (vertical)
STREET2 = (128, 118, 104)         # rua estreita de paralelepípedo
rng = np.random.default_rng(3)

# ------------------------------------------------------------ tempos (áudio cortado)
T = dict(g2=2.76, A=3.70, B=5.82, pensa=8.14, n3=9.05, n2=9.81, n1=10.56, resp=11.23, carA=11.89, semsin=12.73,
         dir=14.59, naoimp=17.23, maior=18.61, larga=19.37, asfalto=20.15, mito=20.99, mito_w=21.47, princ=22.95,
         placa=25.41, regra=26.69, atenc=29.55, duas=30.25, rodov=31.33, rotat=35.43, erro=38.57, aluno=41.29,
         semred=42.57, achando=43.75, pede=45.47, baixa=46.43, redob=47.77, mesmo=49.21, seg=50.97, virar=52.43,
         pedest=53.91, quem=56.23, opedest=58.65, quemja=59.69, dica=62.31, chegou=63.35, odir=64.53, oesq=65.51,
         segue=66.37, salva=68.73, comenta=71.11, sabia=71.97, aoub=73.75, follow=74.69)
T_END = 76.77
SHAKES = [(43.35, 0.35)]

# ------------------------------------------------------------ mapa
def build_map():
    m = paper_texture(W, H, GRASS, 6).convert("RGBA"); d = ImageDraw.Draw(m)
    for _ in range(60):
        x, y, r = int(rng.integers(0, W)), int(rng.integers(0, H)), int(rng.integers(26, 54))
        if abs(y - CY) < WH + r + 8 or abs(x - CX) < NH + r + 8: continue
        d.ellipse([x - r, y - r, x + r, y + r], fill=GRASS2)
    # calçadas
    d.rectangle([0, CY - WH - 26, W, CY + WH + 26], fill=(214, 206, 188))
    d.rectangle([CX - NH - 26, 0, CX + NH + 26, H], fill=(214, 206, 188))
    d.rectangle([CX - NH, 0, CX + NH, H], fill=STREET2)
    for y in range(0, H, 34):                                   # textura de paralelepípedo
        for x in range(CX - NH, CX + NH, 44):
            o = 22 if (y // 34) % 2 else 0
            d.rectangle([x + o, y, x + o + 40, y + 30], outline=(112, 102, 90), width=2)
    d.rectangle([0, CY - WH, W, CY + WH], fill=ROAD)
    for x in range(0, W, 90):                                   # faixa central amarela da rua larga
        if abs(x + 25 - CX) > NH + 40: d.rectangle([x, CY - 5, x + 50, CY + 5], fill=YEL)
    for y in (CY - WH + 6, CY + WH - 10):                       # bordas brancas
        d.rectangle([0, y, CX - NH - 10, y + 4], fill=WHITE); d.rectangle([CX + NH + 10, y, W, y + 4], fill=WHITE)
    # faixa de pedestre na rua estreita, ao sul do cruzamento
    for k in range(6):
        x0 = CX - NH + 8 + k * 37; d.rectangle([x0, CY + WH + 150, x0 + 22, CY + WH + 220], fill=WHITE)
    return m

MAP = build_map()
SPR = {"A": car_sprite((58, 164, 92)), "B": car_sprite(YEL, WHITE)}

def pedestrian(t):
    s = Image.new("RGBA", (90, 90), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    sw = 6 * math.sin(t * 10)
    d.ellipse([12, 30, 78, 62], fill=(60, 90, 170))                  # ombros
    d.ellipse([30 + sw * 0.3, 26, 60 + sw * 0.3, 56], fill=(120, 80, 50))   # cabeça
    return s

# caminhos
B_LANE = CY + 85; A_LANE = CX + 55
P_B_STRAIGHT = Path([(-160, B_LANE), (W + 200, B_LANE)])
P_A_NORTH = Path([(A_LANE, H + 160), (A_LANE, -200)])
P_B_RIGHT = Path([(-160, B_LANE), (CX - NH - 120, B_LANE)] +
                 bezier((CX - NH - 120, B_LANE), (CX - 40, B_LANE), (CX - 55, B_LANE + 40), (CX - 55, CY + WH + 40))[1:] +
                 [(CX - 55, H + 200)])

def s_at_x(path, x):   return (x - path.p[0][0]) / path.L
def s_at_y(path, y):   return (path.p[0][1] - y) / path.L
B_STOP = s_at_x(P_B_STRAIGHT, CX - NH - 120)        # B parado antes do cruzamento
A_STOP = s_at_y(P_A_NORTH, CY + WH + 120)           # A parado antes do cruzamento

def badge(m, x, y, letter, color, s):
    if s <= 0: return
    r = 42 * s; d = ImageDraw.Draw(m)
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE, outline=color, width=max(2, int(8 * s)))
    f = F(SB, max(8, int(58 * s))); w = d.textlength(letter, font=f); d.text((x - w / 2, y - 36 * s), letter, font=f, fill=INK)

def cone(m, x, y, direction, p):
    ov = Image.new("RGBA", m.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    L = 340 * p; sgn = 1 if direction == "dir" else -1        # dir = para baixo (sul), esq = para cima (norte)
    od.polygon([(x + 40, y), (x + 40 + 120 * p, y + sgn * L), (x + 40 + 280 * p, y + sgn * L * 0.8)], fill=(255, 255, 255, 80))
    m.alpha_composite(ov)

def arrow(d, x0, y0, x1, y1, color, w=16):
    d.line([(x0, y0), (x1, y1)], fill=color, width=w)
    a = math.atan2(y1 - y0, x1 - x0)
    d.polygon([(x1 + 30 * math.cos(a), y1 + 30 * math.sin(a)), (x1 + 34 * math.cos(a + 2.3), y1 + 34 * math.sin(a + 2.3)),
               (x1 + 34 * math.cos(a - 2.3), y1 + 34 * math.sin(a - 2.3))], fill=color)

def map_layer(t):
    m = MAP.copy(); d = ImageDraw.Draw(m)
    A, Bs = SPR["A"], SPR["B"]
    if t < T["aluno"]:                                           # quiz, resposta, mito
        sB = drive(t, 0, 3.0, 0, B_STOP, "out") if t < T["dir"] + 0.6 else drive(t, T["dir"] + 0.6, T["dir"] + 3.0, B_STOP, 1.0, "in")
        sA = drive(t, 0.6, 3.6, 0, A_STOP, "out") if t < T["carA"] else drive(t, T["carA"], T["carA"] + 2.4, A_STOP, 1.0, "in")
        if t >= T["naoimp"]: sB, sA = B_STOP, A_STOP                 # volta à cena parada para o mito
        xA, yA, aA = P_A_NORTH.at(sA); xB, yB, aB = P_B_STRAIGHT.at(sB)
        draw_car(m, A, xA, yA, aA); draw_car(m, Bs, xB, yB, aB)
        if t < T["naoimp"]:
            badge(m, xA + 110, yA, "A", GREEN, pop(t, T["A"], 0.3)); badge(m, xB, yB - 110, "B", ORANGE, pop(t, T["B"], 0.3))
        if T["dir"] <= t < T["naoimp"]:                          # seta: "pela sua direita" (do ponto de vista do B)
            p = ease_out(prog(t, T["dir"], T["dir"] + 0.4)); x0, y0 = CX - NH - 120, B_LANE
            if t < T["dir"] + 0.6: arrow(d, x0, y0 + 60, x0 + 40 * p, y0 + 60 + 200 * p, YEL + (255,))
        if T["princ"] <= t < T["regra"]:                         # placa só aparece se existir: mostramos a placa "fantasma"
            a = ease_out(prog(t, T["placa"], T["placa"] + 0.3))
            if a > 0:
                ov = Image.new("RGBA", m.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
                px, py, R = CX + NH + 90, CY + WH + 140, 62
                pts = [(px + R * math.cos(math.radians(22.5 + 45 * i)), py + R * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
                od.rectangle([px - 6, py, px + 6, py + 150], fill=(150, 150, 160, int(255 * a)))
                od.polygon(pts, fill=RED + (int(255 * a),), outline=WHITE + (int(255 * a),), width=6)
                f = F(SB, 32); w = od.textlength("PARE", font=f); od.text((px - w / 2, py - 18), "PARE", font=f, fill=WHITE + (int(255 * a),))
                m.alpha_composite(ov)
    elif t < T["seg"]:                                           # erro na prova: B rápido, quase batida
        if t < 43.35: sB = drive(t, T["aluno"], 43.35, 0, s_at_x(P_B_STRAIGHT, CX - NH - 60), "lin")
        else: sB = s_at_x(P_B_STRAIGHT, CX - NH - 60) + 0.012 * ease_out(prog(t, 43.35, 43.6))
        sA = drive(t, T["aluno"] + 0.4, 43.35, 0, s_at_y(P_A_NORTH, CY + 40), "lin") if t < 43.35 else s_at_y(P_A_NORTH, CY + 40)
        xA, yA, aA = P_A_NORTH.at(sA); xB, yB, aB = P_B_STRAIGHT.at(sB)
        if T["semred"] <= t < 43.35:                             # linhas de velocidade
            for k in range(4): d.line([(xB - 130 - k * 30, yB - 40 + k * 26), (xB - 260 - k * 30, yB - 40 + k * 26)], fill=WHITE + (200,), width=6)
        if t >= 43.35:                                           # marcas de frenagem
            d.line([(xB - 260, yB - 40), (xB - 60, yB - 40)], fill=(30, 30, 30, 180), width=12)
            d.line([(xB - 260, yB + 40), (xB - 60, yB + 40)], fill=(30, 30, 30, 180), width=12)
        draw_car(m, A, xA, yA, aA); draw_car(m, Bs, xB, yB, aB)
    elif t < T["dica"]:                                          # 2ª pergunta: conversão à direita e pedestre
        stop = (CX - 55, CY + WH + 20)
        s_stop = None
        # fração do caminho onde y atinge stop[1] na descida
        ys = P_B_RIGHT.p[:, 1]; idx = int(np.argmax(ys >= stop[1])); s_stop = P_B_RIGHT.cum[idx] / P_B_RIGHT.L
        if t < T["opedest"] + 1.6: sB = drive(t, T["virar"] - 0.6, T["pedest"] + 0.8, 0, s_stop, "out")
        else: sB = drive(t, T["opedest"] + 1.6, T["dica"], s_stop, 1.0, "in")
        blink = int(t * 2.5) % 2 == 0 and t < T["opedest"] + 1.6
        draw_car(m, blinker_sprite(Bs, blink), *P_B_RIGHT.at(sB))
        if t >= T["pedest"]:                                     # pedestre atravessa da direita para a esquerda
            pp = drive(t, T["pedest"], T["opedest"] + 1.5, 0, 1, "lin")
            px = CX + NH + 60 - pp * (2 * NH + 120); py = CY + WH + 185
            ped = pedestrian(t).rotate(90, expand=True); m.alpha_composite(ped, (int(px - 45), int(py - 45)))
    else:                                                        # dica: olha direita, olha esquerda, segue
        if t < T["segue"] + 0.3: sB = drive(t, T["dica"], T["chegou"] + 1.0, 0, B_STOP, "out")
        else: sB = drive(t, T["segue"] + 0.3, T["salva"], B_STOP, 1.0, "in")
        xB, yB, aB = P_B_STRAIGHT.at(sB); draw_car(m, Bs, xB, yB, aB)
        if T["odir"] <= t < T["oesq"]: cone(m, xB, yB, "dir", ease_out(prog(t, T["odir"], T["odir"] + 0.4)))
        if T["oesq"] <= t < T["segue"]: cone(m, xB, yB, "esq", ease_out(prog(t, T["oesq"], T["oesq"] + 0.4)))
    return m

def zoom_for(t):
    k = ease_io(prog(t, T["aluno"] + 1.0, T["semred"] + 0.6)) * (1 - ease_io(prog(t, T["pede"], T["pede"] + 0.6)))
    k2 = ease_io(prog(t, T["virar"], T["virar"] + 0.6)) * (1 - ease_io(prog(t, T["quemja"] + 1.5, T["dica"])))
    z = 1 + 0.25 * k + 0.3 * k2
    return z, (CX - 120 * k - 40 * k2, CY + 40 * k + 200 * k2)

# ------------------------------------------------------------ textos
def top_card(c):
    d = ImageDraw.Draw(c)
    d.rectangle([40, 200, 1040, 336], fill=CARD); d.rectangle([40, 332, 1040, 336], fill=(210, 196, 166))
    f = F(SB, 42); t = "CRUZAMENTO SEM PLACA · QUEM PASSA?"; d.text(((W - d.textlength(t, font=f)) / 2, 216), t, font=f, fill=INK)
    fs = F(SB, 28)
    for x0, txt, col in [(330, "carro A", GREEN), (580, "carro B", ORANGE)]:
        w = d.textlength(txt, font=fs) + 44
        d.rounded_rectangle([x0, 278, x0 + w, 320], 20, fill=col); d.text((x0 + 22, 282), txt, font=fs, fill=WHITE)
    f2 = F(SB, 26); h = "@INSTRUTORGUSTAVOVIEIRA"; d.text(((W - d.textlength(h, font=f2)) / 2, 350), h, font=f2, fill=(245, 245, 235))

def lower(c, t, text, t0, t1, bg, fg=WHITE, rot=-2, y=1450, size=62, **kw):
    if t0 <= t < t1 + 0.2:
        a, dy = slide_in(t, t0, t1); paste_scaled(c, tag(text, size, bg, fg, rot, **kw), (540, y + dy), 1, a)

def at(c, t, text, t0, t1, size, bg, fg, rot, pos, **kw):
    if t0 <= t < t1:
        paste_scaled(c, tag(text, size, bg, fg, rot, **kw), pos, pop(t, t0, 0.3), 1 - prog(t, t1 - 0.2, t1))

STAMPS = {"MITO": stamp_img("MITO", RED), "REDUZ!": stamp_img("REDUZ!", RED), "PEDESTRE": stamp_img("PEDESTRE PRIMEIRO", GREEN, size=60, rot=6)}

def crossed(c, t, text, t0, t1, pos, rot):
    if not (t0 <= t < t1): return
    im = tag(text, 66, WHITE, INK, rot).copy(); d = ImageDraw.Draw(im)
    p = ease_out(prog(t, t0 + 0.3, t0 + 0.55))
    if p > 0: d.line([(30, im.height * 0.55), (30 + (im.width - 60) * p, im.height * 0.45)], fill=RED, width=12)
    paste_scaled(c, im, pos, pop(t, t0, 0.25), 1 - prog(t, t1 - 0.2, t1))

def overlays(c, t):
    at(c, t, "sem placa, sem semáforo", 0.05, T["pensa"], 66, WHITE, INK, 2, (540, 470))
    at(c, t, "quem passa primeiro?", T["g2"], T["pensa"], 84, NAVY, WHITE, -2, (540, 590), hi="passa")
    at(c, t, "A ou B?", T["B"] + 0.8, T["resp"], 120, YEL, INK, 3, (540, 1450))
    if T["pensa"] <= t < T["resp"]:
        p = prog(t, T["pensa"], T["resp"]); dd = ImageDraw.Draw(c)
        paste_scaled(c, tag("pensa rápido!", 70, RED, WHITE, -2), (540, 520), pop(t, T["pensa"], 0.25))
        dd.rounded_rectangle([140, 640, 940, 680], 20, fill=(255, 255, 255, 230)); dd.rounded_rectangle([140, 640, 140 + 800 * (1 - p), 680], 20, fill=RED)
    for txt, t0, t1 in [("3", T["n3"], T["n2"]), ("2", T["n2"], T["n1"]), ("1", T["n1"], T["resp"])]:
        if t0 <= t < t1: paste_scaled(c, tag(txt, 260, WHITE, INK, -3, pad=(60, 20)), (540, 1150), pop(t, t0, 0.22), 1 - prog(t, t1 - 0.12, t1))
    at(c, t, "resposta:", T["resp"], T["semsin"], 70, NAVY, WHITE, -2, (540, 520))
    at(c, t, "CARRO A", T["carA"], T["naoimp"], 110, GREEN, WHITE, 3, (540, 650))
    lower(c, t, "sem sinalização: vale a regra da DIREITA", T["semsin"], T["naoimp"], NAVY, size=50)
    lower(c, t, "não importa se a outra rua é…", T["naoimp"], T["mito"], ORANGE, INK, size=56, y=500)
    crossed(c, t, "MAIOR", T["maior"], T["princ"], (300, 1400), -3)
    crossed(c, t, "mais LARGA", T["larga"], T["princ"], (720, 1500), 3)
    crossed(c, t, "ASFALTADA", T["asfalto"], T["princ"], (420, 1620), -2)
    lower(c, t, "rua principal só tem preferência", T["princ"], T["regra"], NAVY, size=56, y=480)
    lower(c, t, "se tiver PLACA", T["placa"] - 0.3, T["regra"], RED, rot=2, size=70, y=600)
    lower(c, t, "mas atenção: 2 exceções", T["atenc"], T["rodov"], RED, size=72, y=600)
    lower(c, t, "achando que a rua dele é a principal", T["achando"], T["pede"], ORANGE, INK, size=52)
    lower(c, t, "velocidade BAIXA", T["baixa"], T["mesmo"], NAVY, size=72, y=1400)
    lower(c, t, "atenção REDOBRADA", T["redob"], T["mesmo"], RED, rot=2, size=72, y=1530)
    lower(c, t, "mesmo quando a preferência é sua", T["mesmo"], T["seg"], GREEN, size=56)
    at(c, t, "2ª PERGUNTA", T["seg"], T["virar"] + 0.8, 110, YEL, INK, -3, (540, 520))
    lower(c, t, "você vai virar à direita…", T["virar"], T["pedest"], NAVY, size=58)
    lower(c, t, "e o pedestre já começou a atravessar", T["pedest"], T["quem"], ORANGE, INK, size=52)
    if T["quem"] <= t < T["opedest"]:
        on = int((t - T["quem"]) * 3) % 2 == 0
        paste_scaled(c, tag("VOCÊ?", 84, ORANGE if on else WHITE, INK, -3), (300, 1450), pop(t, T["quem"], 0.25))
        paste_scaled(c, tag("PEDESTRE?", 84, WHITE if on else GREEN, INK if on else WHITE, 3), (760, 1450), pop(t, T["quem"] + 0.6, 0.25))
    lower(c, t, "quem já está atravessando tem prioridade", T["quemja"], T["dica"], GREEN, size=48)
    at(c, t, "DICA DE INSTRUTOR", T["dica"], T["segue"], 84, YEL, INK, -2, (540, 520))
    lower(c, t, "olha pra DIREITA", T["odir"], T["oesq"], NAVY, size=72)
    lower(c, t, "olha pra ESQUERDA", T["oesq"], T["segue"], NAVY, rot=2, size=72)
    lower(c, t, "só segue com certeza", T["segue"], T["salva"], GREEN, size=72)
    for key, t0, t1, pos in [("MITO", T["mito_w"], T["princ"], (540, 1000)), ("REDUZ!", 43.35, T["pede"], (540, 560)),
                             ("PEDESTRE", T["opedest"], T["quemja"] + 1.2, (540, 600))]:
        if t0 <= t < t1:
            sc, sh = stamp(t, t0); paste_scaled(c, STAMPS[key], (pos[0] + (sh if int(t * 30) % 2 else -sh), pos[1]), sc, 1 - prog(t, t1 - 0.2, t1))

PAPER_BG = paper_texture(W, H, PAPER, 6).convert("RGBA")

def mini_scene(kind):
    s = Image.new("RGBA", (820, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(s)
    d.rounded_rectangle([0, 0, 819, 519], 28, fill=GRASS)
    if kind == "rodovia":
        d.rectangle([0, 170, 820, 350], fill=ROAD)
        for x in range(0, 820, 90): d.rectangle([x, 256, x + 50, 264], fill=WHITE)
        d.rectangle([520, 0, 600, 170], fill=STREET2)
        car = car_sprite((58, 164, 92)).rotate(-90, expand=True); s.alpha_composite(car, (180, 300 - car.height // 2 - 10))
        car2 = car_sprite(YEL, WHITE); s.alpha_composite(car2.resize((car2.width * 3 // 4, car2.height * 3 // 4)), (515, 20))
        d.rounded_rectangle([40, 30, 330, 120], 14, fill=(20, 110, 60)); d.text((62, 46), "RODOVIA", font=F(SB, 54), fill=WHITE)
    else:
        cx, cy = 410, 260
        d.rectangle([370, 0, 450, 520], fill=ROAD); d.rectangle([0, 220, 820, 300], fill=ROAD)
        d.ellipse([cx - 210, cy - 210, cx + 210, cy + 210], fill=ROAD); d.ellipse([cx - 100, cy - 100, cx + 100, cy + 100], fill=GRASS, outline=WHITE, width=6)
        car = car_sprite((58, 164, 92)).rotate(45, expand=True); car = car.resize((car.width * 3 // 4, car.height * 3 // 4))
        s.alpha_composite(car, (cx + 60, cy + 60))
    return s

MINI = {"rodovia": mini_scene("rodovia"), "rotatoria": mini_scene("rotatoria")}

def fullscreens(c, t):
    def fs(t0, t1, draw):
        if not (t0 <= t < t1): return
        p = ease_out(prog(t, t0, t0 + 0.25)); q = ease_io(prog(t, t1 - 0.25, t1))
        ov = PAPER_BG.copy(); draw(ov)
        c.alpha_composite(ov, (int((1 - p) * W) - int(q * W), 0))
    fs(T["regra"], T["atenc"], lambda ov: (paste_scaled(ov, tag("SEM PLACA", 140, NAVY, WHITE, -3), (540, 820), pop(t, T["regra"], 0.3)),
                                         paste_scaled(ov, tag("= regra da DIREITA", 96, YEL, INK, 3), (540, 1010), pop(t, 27.97, 0.3))))
    def exc(ov):
        k = "rodovia" if t < T["rotat"] else "rotatoria"; t0 = T["rodov"] if k == "rodovia" else T["rotat"]
        paste_scaled(ov, tag("EXCEÇÃO 1" if k == "rodovia" else "EXCEÇÃO 2", 84, RED, WHITE, -3), (540, 480), pop(t, t0, 0.3))
        paste_scaled(ov, MINI[k], (540, 860), pop(t, t0 + 0.2, 0.3))
        txt = "quem está na RODOVIA passa" if k == "rodovia" else "na ROTATÓRIA: quem já circula"
        paste_scaled(ov, tag(txt, 60, GREEN, WHITE, 2), (540, 1220), pop(t, t0 + 1.0 if k == "rodovia" else t0 + 0.9, 0.3))
    fs(T["rodov"], T["erro"], exc)
    fs(T["erro"], T["aluno"], lambda ov: (paste_scaled(ov, tag("o erro que eu mais vejo", 72, WHITE, INK, 2), (540, 820), pop(t, T["erro"], 0.3)),
                                        paste_scaled(ov, tag("na PROVA PRÁTICA", 104, RED, WHITE, -3), (540, 980), pop(t, 39.9, 0.3))))

def end_cards(c, t):
    if t < T["salva"]: return
    a = ease_out(prog(t, T["salva"], T["salva"] + 0.3)); c.alpha_composite(Image.new("RGBA", (W, H), PAPER + (int(235 * a),)))
    if t < T["comenta"]:
        s = pop(t, T["salva"], 0.35); bounce = abs(math.sin((t - T["salva"]) * 5)) * 30 if t > T["salva"] + 0.4 else 0
        icon = Image.new("RGBA", (260, 320), (0, 0, 0, 0)); ImageDraw.Draw(icon).polygon([(30, 20), (230, 20), (230, 300), (130, 220), (30, 300)], fill=YEL, outline=INK, width=10)
        paste_scaled(c, icon, (540, 760 - bounce), s)
        paste_scaled(c, tag("SALVA esse vídeo", 90, NAVY, WHITE, -2), (540, 1060), pop(t, T["salva"] + 0.2, 0.3))
        paste_scaled(c, tag("pra lembrar na hora da prova", 60, WHITE, INK, 2), (540, 1200), pop(t, T["salva"] + 0.9, 0.3))
    elif t < T["follow"]:
        paste_scaled(c, tag("você sabia da regra da direita?", 60, NAVY, WHITE, -2), (540, 640), pop(t, T["sabia"], 0.3))
        paste_scaled(c, tag("A ou B?", 120, YEL, INK, 3), (540, 800), pop(t, T["aoub"], 0.3))
        bx = Image.new("RGBA", (900, 160), (0, 0, 0, 0)); bd = ImageDraw.Draw(bx)
        bd.rounded_rectangle([0, 0, 899, 159], 40, fill=WHITE, outline=(200, 190, 170), width=4); bd.ellipse([24, 30, 124, 130], fill=(200, 200, 205))
        txt = "Não sabia! Era o A"; n = int(clamp((t - T["comenta"] - 0.3) / 0.07, 0, len(txt)))
        bd.text((150, 48), txt[:n] + ("|" if int(t * 3) % 2 == 0 else ""), font=F(INTER, 54), fill=INK)
        send = n >= len(txt) and int(t * 4) % 2 == 0
        bd.ellipse([780, 30, 880, 130], fill=RED if send else (230, 120, 120)); bd.polygon([(808, 55), (858, 80), (808, 105)], fill=WHITE)
        paste_scaled(c, bx, (540, 1040), ease_out(prog(t, T["comenta"], T["comenta"] + 0.3)))
        paste_scaled(c, tag("comenta aí", 64, RED, WHITE, 2), (540, 1220), pop(t, T["comenta"] + 0.3, 0.3))
    else:
        paste_scaled(c, tag("Me segue para mais", 74, NAVY, WHITE, -2), (540, 880), pop(t, T["follow"], 0.3))
        paste_scaled(c, tag("dicas de trânsito", 92, YEL, INK, 2), (540, 1020), pop(t, T["follow"] + 0.35, 0.3))
        q = ease_out(prog(t, T["follow"] + 0.7, T["follow"] + 1.0))
        if q > 0: paste_scaled(c, tag("@instrutorgustavovieira", 52, WHITE, INK, 0, font=INTER), (540, 1200 + (1 - q) * 30), 1, q)

def frame(t):
    c = PAPER_BG.copy(); m = map_layer(t)
    z, (fx, fy) = zoom_for(t)
    if z > 1.001:
        cw, ch = W / z, H / z; x0 = clamp(fx - cw / 2, 0, W - cw); y0 = clamp(fy - ch / 2, 0, H - ch)
        m = m.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    c.alpha_composite(m)
    top_card(c); overlays(c, t); fullscreens(c, t); end_cards(c, t)
    for t0, dur in SHAKES:
        if t0 <= t < t0 + dur:
            k = 1 - (t - t0) / dur; c2 = PAPER_BG.copy(); c2.alpha_composite(c, (int(12 * k * (1 if int(t * 60) % 2 else -1)), int(7 * k * (1 if int(t * 45) % 2 else -1)))); c = c2
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
