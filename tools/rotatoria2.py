"""Rotatória v2 (engajamento): quiz A/B, erro na prova, 2ª pergunta, salvar e comentar. ~69 s, tela cheia.
Uso: python3 rotatoria2.py <saida.mp4> [inicio] [fim] [t1,t2,... => salva PNGs]
Reaproveita o mapa, carros, etiquetas e placas de rotatoria.py.
"""
import math, subprocess, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import rotatoria as R
from rotatoria import (W, H, FPS, F, SB, SBI, INTER, PAPER, CARD, INK, YEL, NAVY, RED, GREEN, WHITE, SPR,
                       CX, CY, R_IN, R_OUT, R_EDGE, STOP_Y, SIGN_POS, SIGNS, Path, entry_path, arc, ring_pt,
                       exit_east_tail, frac_of, tag, paste_scaled, pop, slide_in, stamp, stamp_img, draw_car,
                       drive, dashed_poly, clamp, prog, ease_out, ease_io, blinker_sprite, top_card)
from PIL import Image, ImageDraw

# ------------------------------------------------------------ tempos (áudio cortado, blocos de fala)
B = [0.00, 1.04, 2.11, 3.84, 5.56, 6.54, 7.37, 8.30, 9.09, 10.01, 10.87, 13.99, 15.57, 16.42, 19.75, 20.84,
     21.62, 23.80, 24.32, 26.18, 27.94, 28.98, 29.49, 31.98, 34.88, 39.62, 42.44, 42.97, 43.67, 45.00, 46.15,
     48.19, 49.37, 50.83, 51.71, 53.14, 55.42, 56.50, 59.16, 61.40, 63.73, 64.55, 65.85, 66.75]
T_END = 68.85
T_ESPERA = 14.85          # palavra "espera" (fim do bloco 11)
T_SETA = 56.55
SHAKES = [(T_ESPERA, 0.3), (38.30, 0.35), (B[38], 0.3)]

ORANGE = (226, 168, 0)
P_B = entry_path(R_OUT, exit_theta=-25)                 # carro B (amarelo) entrando pela via sul
F_STOP = frac_of(P_B, STOP_Y)
P_BACK = Path([(R.ENTRY_X, R.MAP_H + 140), (R.ENTRY_X, STOP_Y + 230)])   # carro de trás buzinando
P_SETA = Path(arc(R_OUT, -190, -25) + exit_east_tail(R_OUT, -25))
P_SAI = Path(arc(R_OUT, -150, -25) + exit_east_tail(R_OUT, -25))
P_VOLTA = Path(arc(R_IN, -150, 200))

STAMPS = {"ESPERA": stamp_img("ESPERA", RED), "SETA!": stamp_img("SETA!", (232, 120, 20)),
          "TRAVOU": stamp_img("TRAVOU", RED), "LIVRE": stamp_img("LIVRE", GREEN, rot=6)}

def badge(m, x, y, letter, color, s=1.0):
    if s <= 0: return
    r = 40 * s; d = ImageDraw.Draw(m)
    d.ellipse([x - r - 4, y - r - 4, x + r + 4, y + r + 4], fill=(30, 30, 30, 90))
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE, outline=color, width=max(2, int(8 * s)))
    f = F(SB, max(8, int(56 * s))); w = d.textlength(letter, font=f)
    d.text((x - w / 2, y - 34 * s), letter, font=f, fill=INK)

def clock(m, x, y, t, a):
    d = ImageDraw.Draw(m); r = 46
    d.ellipse([x - r, y - r, x + r, y + r], fill=WHITE + (int(255 * a),), outline=INK + (int(255 * a),), width=6)
    ang = math.radians(t * 360 / 1.2 - 90)
    d.line([(x, y), (x + 34 * math.cos(ang), y + 34 * math.sin(ang))], fill=RED + (int(255 * a),), width=6)
    d.line([(x, y), (x, y - 22)], fill=INK + (int(255 * a),), width=6)

def bubble(m, x, y, text, a):
    if a <= 0: return
    t = tag(text, 44, WHITE, INK, 4, font=INTER); paste_scaled(m, t, (x, y), a)

def lane_band(m, r, color, alpha, width=46):
    ov = Image.new("RGBA", m.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=color + (int(alpha),), width=width)
    m.alpha_composite(ov)

def ring_green(t, offs=(0, 150), r=R_OUT, speed=48, base=200):
    return [(base + speed * t + o) for o in offs]

# ------------------------------------------------------------ mapa por cena
def map_layer(t):
    m = R.STATIC_MAP.copy(); d = ImageDraw.Draw(m)
    G, Y = SPR["g"], SPR["y"]

    if B[14] <= t < B[23]:                                       # placas
        key = "pare" if t < B[19] else "yield"
        paste_scaled(m, SIGNS[key], SIGN_POS, pop(t, B[14] if key == "pare" else B[19], 0.3))

    if t < B[14]:                                                # quiz A x B + resposta
        thA = -175 + 10 * t if t < B[9] else drive(t, B[9], B[11], -175 + 10 * B[9], 10, "io")
        xA, yA, _ = R.ring_car_at(thA); draw_car(m, G, xA, yA, thA)
        if t >= B[9] + 1.5:
            for th in ring_green(t, (150,)): draw_car(m, G, *R.ring_car_at(th))
        xB, yB, aB = P_B.at(F_STOP); draw_car(m, Y, xB, yB, aB)
        badge(m, xA, yA - 105, "A", GREEN, pop(t, B[2], 0.3))
        badge(m, xB + 105, yB, "B", ORANGE, pop(t, B[3], 0.3))
        if B[9] <= t < B[11]:                                    # anel verde no A
            p = ease_out(prog(t, B[9], B[9] + 0.4)); r = 110 + 20 * (1 - p)
            d.ellipse([xA - r, yA - r, xA + r, yA + r], outline=YEL + (int(255 * p),), width=9)
    elif t < B[19]:                                              # PARE
        if t < B[15]: s = drive(t, B[14], B[15] + 0.5, 0, F_STOP, "out")
        elif t < B[18] + 0.6: s = F_STOP
        else: s = drive(t, B[18] + 0.6, B[19] + 0.3, F_STOP, 0.55, "in")
        draw_car(m, Y, *P_B.at(s))
        th = drive(t, B[17] - 0.7, B[18] + 0.5, 190, 330, "lin") if t >= B[17] - 0.7 else 190
        draw_car(m, G, *R.ring_car_at(th))
        x, y, _ = P_B.at(F_STOP)
        if B[16] <= t < B[18] + 0.6 and s >= F_STOP - 1e-4:
            a = int(255 * ease_out(prog(t, B[16], B[16] + 0.3)))
            for dx in (-62, 62):
                for dy in (-50, 50): d.line([(x + dx - 10, y + dy), (x + dx + 10, y + dy)], fill=RED + (a,), width=6)
        if B[17] <= t < B[18] + 0.6:
            p = ease_out(prog(t, B[17], B[17] + 0.4)); ov = Image.new("RGBA", m.size, (0, 0, 0, 0))
            tip = (x - 40 - 300 * p, y - 120 - 140 * p)
            ImageDraw.Draw(ov).polygon([(x - 20, y - 70), tip, (tip[0] + 40, tip[1] + 150)], fill=(255, 255, 255, 70)); m.alpha_composite(ov)
    elif t < B[23]:                                              # DÊ A PREFERÊNCIA
        if t < B[20]: s = drive(t, B[19], B[20], 0, F_STOP * 0.82, "lin")
        elif t < B[22] + 1.2: s = drive(t, B[20], B[22] + 1.2, F_STOP * 0.82, F_STOP, "out")
        else: s = drive(t, B[22] + 1.2, B[23] + 0.3, F_STOP, 0.55, "in")
        draw_car(m, Y, *P_B.at(s))
        th = drive(t, B[22] - 0.6, B[22] + 1.6, 175, 340, "lin") if t >= B[22] - 0.6 else 175
        draw_car(m, G, *R.ring_car_at(th))
    elif t < B[29]:                                              # erro na prova (pista livre, aluno travado)
        if t < B[28]: s = drive(t, B[24], B[24] + 1.4, 0, F_STOP, "out")
        else: s = drive(t, B[28], B[29] + 0.4, F_STOP, 0.5, "io")
        x, y, a = P_B.at(s); draw_car(m, Y, x, y, a)
        if t >= B[25]:                                           # carro de trás
            sb = drive(t, B[25], B[25] + 1.0, 0, 1, "out")
            if t >= B[28]: sb = 1
            xb, yb, ab = P_BACK.at(sb); draw_car(m, G, xb, yb, ab)
            bubble(m, xb - 170, yb - 30, "BI BI!", pop(t, B[25] + 1.0, 0.25) * (1 - prog(t, B[26] - 0.3, B[26])))
        if 36.4 <= t < B[26]:
            clock(m, x - 150, y - 20, t, ease_out(prog(t, 36.4, 36.7)) * (1 - prog(t, B[26] - 0.3, B[26])))
        if B[26] <= t < B[28]:
            p = ease_out(prog(t, B[26], B[26] + 0.4)); ov = Image.new("RGBA", m.size, (0, 0, 0, 0))
            tip = (x - 40 - 300 * p, y - 120 - 140 * p)
            ImageDraw.Draw(ov).polygon([(x - 20, y - 70), tip, (tip[0] + 40, tip[1] + 150)], fill=(255, 255, 255, 70)); m.alpha_composite(ov)
    elif t < B[36]:                                              # 2ª pergunta: faixas
        if t < B[31]:
            p = 0.5 + 0.5 * math.sin((t - B[30]) * 6) if t >= B[30] else 0      # seta pulsando na próxima saída
            if t >= B[30]:
                ex, ey = CX + R_EDGE + 150, CY + R.LANE
                d.polygon([(ex + 60, ey), (ex - 20, ey - 50), (ex - 20, ey + 50)], fill=YEL + (int(140 + 115 * p),))
                d.rectangle([ex - 110, ey - 18, ex - 20, ey + 18], fill=YEL + (int(140 + 115 * p),))
        if B[31] <= t < B[33]:                                   # faixas piscando com "?"
            on = int((t - B[31]) * 3) % 2 == 0
            lane_band(m, R_OUT, YEL, 170 if on else 70); lane_band(m, R_IN, WHITE, 70 if on else 170)
        if B[33] <= t < B[36]:
            lane_band(m, R_OUT, GREEN, 150 * ease_out(prog(t, B[34], B[34] + 0.3)))
        if t >= B[35]:
            pv = drive(t, B[35], B[36], 0, 1, "io"); dashed_poly(d, P_VOLTA.upto(pv), WHITE + (230,), 8)
            draw_car(m, G, *P_VOLTA.at(pv))
        sB = 0 if t < B[34] else drive(t, B[34], B[35] + 1.2, 0, 1, "io")
        draw_car(m, Y, *P_SAI.at(sB))
        if B[31] <= t < B[33]:
            xb, yb, _ = P_SAI.at(0)
            badge(m, *ring_pt(R_OUT + 120, -112), "?", ORANGE, pop(t, B[31], 0.25))
    elif t < B[39]:                                              # seta
        s = drive(t, B[36], B[38] - 0.2, 0, 1, "io")
        blink = t >= B[36] + 0.5 and int((t - B[36]) * 2.5) % 2 == 0
        draw_car(m, blinker_sprite(Y, blink), *P_SETA.at(s))
        for th in ring_green(t, (60, 210)): draw_car(m, G, *R.ring_car_at(th, R_IN))
    else:
        for th in ring_green(t): draw_car(m, G, *R.ring_car_at(th))
    return m

def zoom_for(t):
    zin = ease_io(prog(t, B[14] - 0.6, B[14] + 0.2)); zout = ease_io(prog(t, B[23], B[23] + 0.6))
    k = zin * (1 - zout)
    # zoom leve no "erro": aproxima do aluno travado
    k2 = ease_io(prog(t, B[24] + 1.0, B[24] + 1.8)) * (1 - ease_io(prog(t, B[28], B[29])))
    z = 1 + 0.32 * k + 0.22 * k2
    fy = CY + 330 * max(k, k2 * 1.2)
    return z, (CX + 60 * max(k, k2), fy)

# ------------------------------------------------------------ textos sobre a tela
def lower(c, t, text, t0, t1, bg, fg=WHITE, rot=-2, y=1440, size=64, **kw):
    if t0 <= t < t1 + 0.2:
        a, dy = slide_in(t, t0, t1); paste_scaled(c, tag(text, size, bg, fg, rot, **kw), (540, y + dy), 1, a)

def big_number(c, t, text, t0, t1, color=WHITE, fg=INK, size=260):
    if t0 <= t < t1:
        s = pop(t, t0, 0.22); a = 1 - prog(t, t1 - 0.12, t1)
        paste_scaled(c, tag(text, size, color, fg, -3, pad=(60, 20)), (540, 1000), s, a)

def overlays(c, t):
    # gancho / quiz
    if t < B[4]:
        a1 = pop(t, 0.05, 0.25); a2 = pop(t, B[1], 0.25); fade = 1 - prog(t, B[4] - 0.2, B[4])
        paste_scaled(c, tag("Na rotatória,", 76, WHITE, INK, 2), (540, 470), a1, fade)
        paste_scaled(c, tag("quem passa primeiro?", 84, NAVY, WHITE, -2, hi="passa"), (540, 590), a2, fade)
    if B[3] <= t < B[9]:
        paste_scaled(c, tag("A ou B?", 120, YEL, INK, 3), (540, 1440), pop(t, B[3] + 0.6, 0.3), 1 - prog(t, B[9] - 0.2, B[9]))
    if B[4] <= t < B[8]:                                        # barra do tempo
        p = prog(t, B[4], B[8]); dd = ImageDraw.Draw(c)
        paste_scaled(c, tag("pensa rápido!", 70, RED, WHITE, -2), (540, 520), pop(t, B[4], 0.25))
        dd.rounded_rectangle([140, 640, 940, 680], 20, fill=(255, 255, 255, 230))
        dd.rounded_rectangle([140, 640, 140 + 800 * (1 - p), 680], 20, fill=RED)
    big_number(c, t, "3", B[5], B[6]); big_number(c, t, "2", B[6], B[7]); big_number(c, t, "1", B[7], B[8])
    if B[8] <= t < B[11]:
        paste_scaled(c, tag("resposta:", 70, NAVY, WHITE, -2), (540, 520), pop(t, B[8], 0.25), 1 - prog(t, B[11] - 0.2, B[11]))
        if t >= B[9]:
            paste_scaled(c, tag("CARRO A", 110, GREEN, WHITE, 3), (540, 650), pop(t, B[9], 0.3), 1 - prog(t, B[11] - 0.2, B[11]))
    lower(c, t, "quem já está dentro tem a preferência", B[10] + 0.3, B[11], GREEN, size=56)
    lower(c, t, "quem vai entrar…", B[11], B[12], ORANGE, INK, 2)
    lower(c, t, "mas atenção:", B[12], B[13], NAVY)
    lower(c, t, "PARE: para totalmente", B[14] + 0.2, B[16], RED)
    lower(c, t, "rodas 100% paradas", B[16], B[17], RED, rot=2)
    lower(c, t, "olha à esquerda e entra quando estiver livre", B[17], B[19] - 0.1, NAVY, size=48)
    lower(c, t, "DÊ A PREFERÊNCIA: reduz", B[19], B[22], RED, size=58)
    lower(c, t, "e deixa passar quem já está dentro", B[22], B[23], GREEN, rot=2, size=54)
    lower(c, t, "com medo… e a pista LIVRE", 36.4, B[25], ORANGE, INK, size=58, y=770)
    lower(c, t, "atrapalha o trânsito", B[25], 41.0, RED, rot=2, y=770)
    lower(c, t, "e pesa na avaliação", 41.0, B[26], RED, y=770)
    lower(c, t, "olhou, está livre? pode entrar", B[26], B[29], GREEN, size=58, y=770)
    if B[29] <= t < B[31]:
        paste_scaled(c, tag("2ª PERGUNTA", 110, YEL, INK, -3), (540, 520), pop(t, B[29], 0.3), 1 - prog(t, B[31] - 0.2, B[31]))
    lower(c, t, "você vai sair na próxima saída", B[30], B[31], NAVY, size=58)
    if B[31] <= t < B[33]:
        paste_scaled(c, tag("DIREITA ou ESQUERDA?", 76, NAVY, WHITE, 2), (540, 1440), pop(t, B[31], 0.3))
    if B[33] <= t < B[35]:
        paste_scaled(c, tag("faixa da DIREITA", 84, GREEN, WHITE, -2), (540, 1440), pop(t, B[34], 0.3))
    lower(c, t, "esquerda: volta maior", B[35], B[36], NAVY, rot=2, y=1440)
    lower(c, t, "seta para a direita antes de sair", B[36], B[38], ORANGE, INK, size=56)
    lower(c, t, "sem seta = infração", B[38], B[39], RED, rot=2, size=72)
    for key, t0, t1, pos in [("ESPERA", T_ESPERA, B[12], (250, 1250)), ("TRAVOU", 38.30, B[25] + 0.8, (540, 490)),
                             ("LIVRE", B[27], B[28] + 0.5, (540, 490)), ("SETA!", T_SETA, B[38], (270, 420))]:
        if t0 <= t < t1:
            sc, sh = stamp(t, t0); fade = 1 - prog(t, t1 - 0.2, t1)
            paste_scaled(c, STAMPS[key], (pos[0] + (sh if int(t * 30) % 2 else -sh), pos[1]), sc, fade)

def fullscreen(c, t, t0, t1, lines):
    if not (t0 <= t < t1): return
    p = ease_out(prog(t, t0, t0 + 0.25)); q = 1 - ease_io(prog(t, t1 - 0.25, t1))
    ov = R.PAPER_BG.copy(); x = int((1 - p) * W) if p < 1 else 0
    for (text, size, bg, fg, rot, y, delay, kw) in lines:
        paste_scaled(ov, tag(text, size, bg, fg, rot, **kw), (540, y), pop(t, t0 + delay, 0.3))
    if q < 1: x = -int((1 - q) * W)
    c.alpha_composite(ov, (x, 0))

def end_cards(c, t):
    if t < B[39]: return
    a = ease_out(prog(t, B[39], B[39] + 0.3))
    ov = Image.new("RGBA", (W, H), PAPER + (int(235 * a),)); c.alpha_composite(ov)
    d = ImageDraw.Draw(c)
    if t < B[40]:                                                # salvar
        s = pop(t, B[39], 0.35); bounce = abs(math.sin((t - B[39]) * 5)) * 30 if t > B[39] + 0.4 else 0
        icon = Image.new("RGBA", (260, 320), (0, 0, 0, 0)); idr = ImageDraw.Draw(icon)
        idr.polygon([(30, 20), (230, 20), (230, 300), (130, 220), (30, 300)], fill=YEL, outline=INK, width=10)
        paste_scaled(c, icon, (540, 760 - bounce), s)
        paste_scaled(c, tag("SALVA esse vídeo", 90, NAVY, WHITE, -2), (540, 1060), pop(t, B[39] + 0.2, 0.3))
        paste_scaled(c, tag("pra lembrar na hora da prova", 60, WHITE, INK, 2), (540, 1200), pop(t, B[39] + 0.9, 0.3))
    elif t < B[43]:                                              # comentar
        paste_scaled(c, tag("você acertou a 1ª?", 80, NAVY, WHITE, -2), (540, 640), pop(t, B[40], 0.3))
        paste_scaled(c, tag("A ou B?", 120, YEL, INK, 3), (540, 800), pop(t, B[42], 0.3))
        bx = Image.new("RGBA", (900, 160), (0, 0, 0, 0)); bd = ImageDraw.Draw(bx)
        bd.rounded_rectangle([0, 0, 899, 159], 40, fill=WHITE, outline=(200, 190, 170), width=4)
        bd.ellipse([24, 30, 124, 130], fill=(200, 200, 205))
        txt = "Acertei! Era o A"; n = int(clamp((t - B[41]) / 0.07, 0, len(txt))); shown = txt[:n]
        bd.text((150, 48), shown + ("|" if int(t * 3) % 2 == 0 else ""), font=F(INTER, 54), fill=INK)
        send = n >= len(txt) and int(t * 4) % 2 == 0
        bd.ellipse([780, 30, 880, 130], fill=RED if send else (230, 120, 120))
        bd.polygon([(808, 55), (858, 80), (808, 105)], fill=WHITE)
        paste_scaled(c, bx, (540, 1040), ease_out(prog(t, B[40], B[40] + 0.3)))
        paste_scaled(c, tag("comenta aí 👇".replace(" 👇", ""), 64, RED, WHITE, 2), (540, 1220), pop(t, B[40] + 0.3, 0.3))
    else:                                                        # seguir
        paste_scaled(c, tag("Me segue para mais", 74, NAVY, WHITE, -2), (540, 880), pop(t, B[43], 0.3))
        paste_scaled(c, tag("dicas de trânsito", 92, YEL, INK, 2), (540, 1020), pop(t, B[43] + 0.35, 0.3))
        q = ease_out(prog(t, B[43] + 0.7, B[43] + 1.0))
        if q > 0: paste_scaled(c, tag("@instrutorgustavovieira", 52, WHITE, INK, 0, font=INTER), (540, 1200 + (1 - q) * 30), 1, q)

def shake_off(t):
    for t0, dur in SHAKES:
        if t0 <= t < t0 + dur:
            k = 1 - (t - t0) / dur; return int(10 * k * (1 if int(t * 60) % 2 else -1)), int(6 * k * (1 if int(t * 45) % 2 else -1))
    return 0, 0

def frame(t):
    c = R.PAPER_BG.copy(); m = map_layer(t)
    z, (fx, fy) = zoom_for(t)
    if z > 1.001:
        cw, ch = W / z, R.MAP_H / z
        x0 = clamp(fx - cw / 2, 0, W - cw); y0 = clamp(fy - ch / 2, 0, R.MAP_H - ch)
        m = m.resize((W, R.MAP_H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    c.alpha_composite(m, (0, R.MAP_Y0))
    top_card(c)
    d = ImageDraw.Draw(c); f = F(SB, 26)
    d.text(((W - d.textlength(R.HANDLE, font=f)) / 2, 350), R.HANDLE, font=f, fill=(245, 245, 235))
    overlays(c, t)
    fullscreen(c, t, B[13] + 0.2, B[14] - 0.1, [
        ("vale o que", 110, NAVY, WHITE, -3, 820, 0.1, {}),
        ("a PLACA", 170, YEL, INK, 3, 1010, 0.6, {}),
        ("manda", 110, NAVY, WHITE, -2, 1200, 1.4, {})])
    fullscreen(c, t, B[23], B[24], [
        ("o erro que eu mais vejo", 72, WHITE, INK, 2, 820, 0.1, {}),
        ("na PROVA PRÁTICA", 104, RED, WHITE, -3, 980, 0.9, {})])
    end_cards(c, t)
    dx, dy = shake_off(t)
    if dx or dy:
        c2 = R.PAPER_BG.copy(); c2.alpha_composite(c, (dx, dy)); c = c2
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
