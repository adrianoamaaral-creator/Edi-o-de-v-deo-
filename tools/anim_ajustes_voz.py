"""Flor de Lótus · "Como funcionam os ajustes" — versão com narração.

As cenas seguem os tempos da fala já sem pausas (tempos em segundos do áudio cortado).
Uso: python3 tools/anim_ajustes_voz.py SAIDA.mp4 [DURACAO] [INICIO]
"""
import math
import subprocess
import sys
from multiprocessing import Pool

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import anim_ajustes as A  # noqa: E402
from anim_ajustes import (BRANCO, CINZA, FPS, H, ROSA, S, W, check_row, clamp,  # noqa: E402
                          draw_garment, ease, fade, font, layer, line, partial, prog,
                          quad, spaced, text_parts, tf)

DUR = 60.4

# --------------------------------------------------------------- tempos (fala)
T = dict(
    hook_out=3.25, ajusta=2.5,
    vest_in=3.4, barra=5.7, alca=6.47, cintura=7.29, vest_out=7.7,
    terno_in=7.95, punho=10.02, barra_calca=10.85, pinca=12.61, terno_out=13.15,
    st_in=13.4, todos=14.37, carimbo=16.89, st_out=17.5,
    p1_in=17.75, dias=17.89, contato=20.45, medidas=23.0, p1_out=24.4,
    dica_in=24.6, sapato=27.37, s_vest=30.0, s_terno=31.14, dica_out=31.65,
    p2_in=31.85, ajustes=32.54, higien=33.76, passad=35.07, impec=37.99, p2_out=38.9,
    p3_in=39.1, horario=41.1, p3_out=42.75,
    p4_in=42.95, lavar=45.17, passar=46.19, capinha=47.6, trazer=50.16, p4_out=50.85,
    final=51.05,
)

SONS = [  # (som, tempo, volume dB)
    ("whoosh", 0.0, -15), ("whoosh", T["vest_in"], -17),
    ("pop", T["barra"] + 0.2, -15), ("pop", T["alca"] + 0.2, -15), ("pop", T["cintura"] + 0.2, -15),
    ("whoosh", T["terno_in"] - 0.1, -17),
    ("pop", T["punho"] + 0.2, -15), ("pop", T["barra_calca"] + 0.2, -15), ("pop", T["pinca"] + 0.2, -15),
    ("whoosh", T["st_in"], -17), ("impacto", T["carimbo"] + 0.15, -10),
    ("whoosh", T["p1_in"], -17), ("tique", T["dias"] + 0.8, -14), ("ding", T["contato"] + 0.3, -15),
    ("whoosh", T["dica_in"], -17), ("pop", T["sapato"] + 0.3, -15),
    ("whoosh", T["p2_in"], -17), ("pop", T["higien"] + 0.2, -15), ("pop", T["passad"] + 0.2, -15),
    ("ding", T["impec"] + 0.2, -17),
    ("whoosh", T["p3_in"], -17), ("tique", T["horario"] + 0.3, -14),
    ("whoosh", T["p4_in"], -17), ("pop", T["lavar"] + 0.2, -15), ("pop", T["passar"] + 0.2, -15),
    ("whoosh", T["capinha"] + 0.2, -17), ("ding", T["final"] + 0.2, -15),
]


def scene_alpha(t, t_in, t_out, d=0.3):
    return fade(t, t_in, t_out, d, d)


def pill(d, t, t_in, t_out, txt):
    a = scene_alpha(t, t_in, t_out)
    if a <= 0:
        return
    dy = -30 * (1 - ease(prog(t, t_in, 0.3)))
    f = font("inter", 28)
    sp = 0.18 * 28 * S
    tw = sum(d.textlength(c, font=f) for c in txt) + sp * (len(txt) - 1)
    w = tw / S + 64
    x0, y0 = 540 - w / 2, 262 + dy
    d.rounded_rectangle((x0 * S, y0 * S, (x0 + w) * S, (y0 + 56) * S), 28 * S,
                        outline=ROSA + (int(255 * a),), width=int(2 * S))
    spaced(d, 540, y0 + 39, txt, 28, ROSA, a, 0.18)


# --------------------------------------------------------------- desenhos extras

def heel(ox, oy, k=1.25):
    P = lambda pts: [(ox + x * k, oy + y * k) for x, y in pts]
    return [
        P(quad((8, 150), (30, 112), (95, 104), 16)),           # bico até o peito do pé
        P(quad((95, 104), (130, 116), (150, 112), 10)),         # decote
        P(quad((150, 112), (205, 70), (232, 34), 14)),          # subida do calcanhar
        P([(232, 34), (246, 40), (242, 92)]),                   # traseira
        P([(242, 92), (232, 186), (222, 186), (214, 112)]),     # salto agulha
        P(quad((214, 112), (140, 132), (60, 160), 16)),         # sola (arco)
        P(quad((60, 160), (14, 170), (8, 150), 8)),             # ponta
    ]


def oxford(ox, oy, k=1.25):
    P = lambda pts: [(ox + x * k, oy + y * k) for x, y in pts]
    return [
        P(quad((4, 160), (6, 118), (60, 104), 14)),             # bico
        P(quad((60, 104), (120, 92), (150, 70), 12)),           # gáspea
        P([(150, 70), (205, 66), (236, 78)]),                   # boca
        P(quad((236, 78), (252, 110), (248, 160), 10)),         # calcanhar
        P([(4, 160), (248, 160), (248, 176), (8, 176), (4, 160)]),  # sola
        P([(196, 160), (196, 176)]),                            # salto
        P([(126, 88), (142, 102)]), P([(138, 80), (154, 94)]), P([(150, 72), (166, 86)]),  # cadarço
    ]


def clock(cx, cy, r, p, t):
    pts = [(cx + r * math.cos(math.radians(-90 + 360 * u / 60)), cy + r * math.sin(math.radians(-90 + 360 * u / 60)))
           for u in range(61)]
    return pts


def star(d, cx, cy, r, a):
    if a <= 0 or r <= 0:
        return
    pts = []
    for i in range(8):
        ang = math.pi / 4 * i - math.pi / 2
        rr = r if i % 2 == 0 else r * 0.28
        pts.append(((cx + rr * math.cos(ang)) * S, (cy + rr * math.sin(ang)) * S))
    d.polygon(pts, fill=ROSA + (int(255 * a),))


def xrow(d, t, ti, y, label, a_out, x=300):
    p = prog(t, ti, 0.2)
    if p <= 0:
        return
    a = ease(p) * a_out
    off = -40 * (1 - ease(p))
    cx, cy, r = x + 24 + off, y - 17, 24
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), outline=ROSA + (int(255 * a),), width=int(3 * S))
    pk = ease(prog(t, ti + 0.05, 0.2))
    for (x1, y1), (x2, y2) in (((cx - 9, cy - 9), (cx + 9, cy + 9)), ((cx + 9, cy - 9), (cx - 9, cy + 9))):
        line(d, partial([(x1, y1), (x2, y2)], pk), ROSA, 3.4, a)
    text_parts(d, y, [(label, False)], 52, a, x0=x + 66 + off, fonts=("pf6", "pf6i"))


# --------------------------------------------------------------- cenas

def scene_hook(t):
    if t > T["hook_out"] + 0.3:
        return None
    a_out = 1 - ease(prog(t, T["hook_out"], 0.25))
    p = ease(prog(t, 0.0, 0.13))
    s = 0.9 + 0.1 * p
    tmp, td = layer()
    text_parts(td, 600, [("O vestido ou o terno", False)], 92, 1.0)
    text_parts(td, 740, [("ficou ", False), ("grande", True), ("?", False)], 118, 1.0)
    a2 = fade(t, T["ajusta"], None, 0.3)
    text_parts(td, 930, [("A gente ", False), ("ajusta", True), (".", False)], 78, a2, fonts=("pf6", "pf6i"))
    lp = ease(prog(t, T["ajusta"] + 0.1, 0.4))
    if lp > 0:
        line(td, [(540 - 120 * lp, 1000), (540 + 120 * lp, 1000)], ROSA, 2, a2)
    if s != 1:
        sm = tmp.resize((int(W * S * s), int(H * S * s)), Image.BILINEAR)
        tmp = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        tmp.paste(sm, ((W * S - sm.width) // 2, (H * S - sm.height) // 2))
    a = p * a_out
    if a < 1:
        tmp.putalpha(tmp.split()[3].point(lambda v: int(v * a)))
    return tmp


VEST = [("barra", T["barra"], "Barra"), ("alca", T["alca"], "Alça"), ("cintura", T["cintura"], "Cintura")]
TERN = [("punho", T["punho"], "Punho"), ("barra_calca", T["barra_calca"], "Barra da calça"),
        ("pinca", T["pinca"], "Pinça na cintura")]
ROWS = [1335, 1420, 1505]


def scene_garments(d, gd, t):
    if T["vest_in"] - 0.1 <= t <= T["vest_out"] + 0.35:
        A.title_block(d, t, T["vest_in"], T["vest_out"], "COMO FUNCIONAM OS AJUSTES", [("No ", False), ("vestido", True)])
        draw_garment(d, gd, t, A.VESTIDO, T["vest_in"] + 0.05, [(n, ti) for n, ti, _ in VEST], T["vest_out"], 0)
        a_out = 1 - ease(prog(t, T["vest_out"], 0.3))
        for (n, ti, lab), y in zip(VEST, ROWS):
            check_row(d, t, ti, y, lab, a_out)
            if n == "cintura" and t >= ti:
                for a, b in A.SETAS_VESTIDO:
                    A.arrow(d, tf([a])[0], tf([b])[0], ROSA, a_out, ease(prog(t, ti + 0.1, 0.3)))
    if T["terno_in"] - 0.1 <= t <= T["terno_out"] + 0.35:
        A.title_block(d, t, T["terno_in"], T["terno_out"], "COMO FUNCIONAM OS AJUSTES", [("No ", False), ("terno", True)])
        draw_garment(d, gd, t, A.TERNO, T["terno_in"] + 0.05, [(n, ti) for n, ti, _ in TERN], T["terno_out"], 0)
        a_out = 1 - ease(prog(t, T["terno_out"], 0.3))
        pb = ease(prog(t, T["terno_in"] + 0.9, 0.3))
        for bx, by in A.BOTOES:
            (x, y), = tf([(bx, by)])
            r = 5 * S
            d.ellipse((x * S - r, y * S - r, x * S + r, y * S + r), outline=BRANCO + (int(230 * pb * a_out),), width=int(2.4 * S))
        for (n, ti, lab), y in zip(TERN, ROWS):
            check_row(d, t, ti, y, lab, a_out)
            if n == "pinca" and t >= ti:
                for a, b in A.SETAS_TERNO:
                    A.arrow(d, tf([a])[0], tf([b])[0], ROSA, a_out, ease(prog(t, ti + 0.1, 0.3)))


def scene_stamp(d, base, t):
    t0, t_out = T["st_in"], T["st_out"]
    if t < t0 or t > t_out + 0.35:
        return
    a = scene_alpha(t, t0, t_out)
    text_parts(d, 620, [("E o ", False), ("melhor", True), ("...", False)], 72, a, fonts=("pf6", "pf6i"))
    a2 = scene_alpha(t, T["todos"], t_out)
    text_parts(d, 740, [("Todos os ", False), ("ajustes", True)], 92, a2)
    ts = T["carimbo"]
    if t >= ts:
        p = prog(t, ts, 0.18)
        s = 1.6 - 0.65 * ease(p / 0.75) if p < 0.75 else 0.95 + 0.05 * ease((p - 0.75) / 0.25)
        aa = clamp((t - ts) / 0.08) * (1 - ease(prog(t, t_out, 0.3)))
        st = Image.new("RGBA", (760 * S, 300 * S), (0, 0, 0, 0))
        sd = ImageDraw.Draw(st)
        sd.rounded_rectangle((10 * S, 10 * S, 750 * S, 290 * S), 18 * S, outline=ROSA + (255,), width=9 * S)
        sd.text((380 * S, 150 * S), "INCLUSO", font=font("inter", 104), fill=ROSA + (255,), anchor="ms")
        sd.text((380 * S, 232 * S), "NO ALUGUEL", font=font("inter", 46), fill=ROSA + (255,), anchor="ms")
        st = st.rotate(8, resample=Image.BICUBIC, expand=True)
        st = st.resize((int(st.width * s), int(st.height * s)), Image.BICUBIC)
        if aa < 1:
            st.putalpha(st.split()[3].point(lambda v: int(v * aa)))
        base.alpha_composite(st, (540 * S - st.width // 2, 1000 * S - st.height // 2))


def scene_p1(d, base, t):
    t0, t_out = T["p1_in"], T["p1_out"]
    if t < t0 - 0.05 or t > t_out + 0.35:
        return
    pill(d, t, t0, t_out, "PASSO 1 · MEDIDAS")
    a = scene_alpha(t, t0, t_out)
    n = round(15 * ease(prog(t, T["dias"], 0.8)))
    d.text((540 * S, 700 * S), f"{n:02d}", font=font("pfi", 300), fill=ROSA + (int(255 * a),), anchor="ms")
    text_parts(d, 800, [("dias antes", False)], 84, a)
    spaced(d, 540, 870, "DA RETIRADA DO TRAJE", 30, CINZA, a, 0.18, "inter6")
    # notificação
    tn = T["contato"]
    if t >= tn:
        p = ease(prog(t, tn, 0.35))
        an = p * (1 - ease(prog(t, t_out, 0.3)))
        y0 = 1000 - 200 * (1 - p)
        card, cd = layer()
        cd.rounded_rectangle((130 * S, y0 * S, 950 * S, (y0 + 190) * S), 34 * S, fill=(246, 241, 241, 255))
        r = 46
        cx, cy = 210, y0 + 95
        cd.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=(20, 18, 19, 255))
        lg = A.LOGO_IM.crop((0, 0, int(A.LOGO_IM.height * 1.05), A.LOGO_IM.height))
        lg = lg.resize((int(70 * S), int(70 * S * lg.height / lg.width)), Image.LANCZOS)
        card.alpha_composite(lg, (int(cx * S - lg.width / 2), int(cy * S - lg.height / 2)))
        cd.text((285 * S, (y0 + 78) * S), "Flor de Lótus", font=font("inter", 36), fill=(30, 26, 28, 255), anchor="ls")
        cd.text((870 * S, (y0 + 78) * S), "agora", font=font("inter6", 26), fill=(140, 130, 132, 255), anchor="rs")
        cd.text((285 * S, (y0 + 132) * S), "Vamos agendar sua tirada de medidas?", font=font("inter6", 30),
                fill=(70, 62, 66, 255), anchor="ls")
        if an < 1:
            card.putalpha(card.split()[3].point(lambda v: int(v * an)))
        base.alpha_composite(card)
    am = scene_alpha(t, T["medidas"], t_out)
    if am > 0:
        text_parts(d, 1330, [("A loja ", False), ("agenda com você", True)], 60, am, fonts=("pf6", "pf6i"))


def scene_dica(d, gd, t):
    t0, t_out = T["dica_in"], T["dica_out"]
    if t < t0 - 0.05 or t > t_out + 0.35:
        return
    pill(d, t, t0, t_out, "DICA")
    a = scene_alpha(t, t0 + 0.4, t_out)
    text_parts(d, 420, [("Traga o ", False), ("sapato", True)], 92, a)
    text_parts(d, 510, [("que você vai usar na festa", False)], 54, a * 0.9, fonts=("pf6", "pf6i"))
    p = ease(prog(t, T["sapato"], 1.0))
    for shape, ox, ti, lab in ((heel(110, 780, 1.55), 110, T["s_vest"], "vestido"), (oxford(580, 820, 1.5), 580, T["s_terno"], "terno")):
        for pts in shape:
            line(d, partial(pts, p), BRANCO, 3.2, 0.92 * a)
        hp = prog(t, ti, 0.4)
        if hp > 0:
            for pts in shape:
                line(gd, partial(pts, ease(hp)), ROSA, 14, 0.8 * a)
            al = ease(hp) * a
            text_parts(d, 1150, [("para o ", False), (lab, True)], 52, al, cx=ox + 190, fonts=("pf6", "pf6i"))


def scene_p2(d, t):
    t0, t_out = T["p2_in"], T["p2_out"]
    if t < t0 - 0.05 or t > t_out + 0.35:
        return
    pill(d, t, t0, t_out, "PASSO 2 · CUIDADO")
    a = scene_alpha(t, t0, t_out)
    text_parts(d, 420, [("Depois dos ", False), ("ajustes", True)], 84, a)
    a_out = 1 - ease(prog(t, t_out, 0.3))
    for ti, y, lab in ((T["ajustes"], 640, "Ajustes"), (T["higien"], 740, "Higienização"), (T["passad"], 840, "Passadoria")):
        check_row(d, t, ti, y, lab, a_out, x=330)
    ai = scene_alpha(t, T["impec"], t_out)
    if ai > 0:
        text_parts(d, 1090, [("Seu traje ", False), ("impecável", True)], 88, ai)
        for i, (sx, sy, sr, dl) in enumerate(((170, 990, 30, 0.0), (930, 1010, 24, 0.15), (880, 1150, 18, 0.3),
                                               (210, 1160, 20, 0.45), (540, 1210, 16, 0.6))):
            tt = t - T["impec"] - dl
            if tt > 0:
                r = sr * (ease(clamp(tt / 0.3)) * (0.85 + 0.15 * math.sin(tt * 5)))
                star(d, sx, sy, r, ai)


def scene_p3(d, t):
    t0, t_out = T["p3_in"], T["p3_out"]
    if t < t0 - 0.05 or t > t_out + 0.35:
        return
    pill(d, t, t0, t_out, "PASSO 3 · RETIRADA")
    a = scene_alpha(t, t0, t_out)
    text_parts(d, 420, [("Na hora de ", False), ("buscar", True)], 84, a)
    p = ease(prog(t, t0 + 0.3, 1.0))
    cx, cy, r = 540, 760, 170
    pts = clock(cx, cy, r, p, t)
    line(d, partial(pts, p), BRANCO, 3.2, 0.92 * a)
    for i in range(12):
        ang = math.radians(-90 + 30 * i)
        ap = clamp(p * 12 - i)
        if ap > 0:
            line(d, [(cx + (r - 22) * math.cos(ang), cy + (r - 22) * math.sin(ang)),
                     (cx + (r - 8) * math.cos(ang), cy + (r - 8) * math.sin(ang))], BRANCO, 3, 0.7 * a * ap)
    hp = ease(prog(t, t0 + 0.8, 1.2))
    hm = math.radians(-90 + 360 * (0.5 * hp))  # ponteiro dos minutos vai até :30
    hh = math.radians(-90 + 30 * (1 + 0.5 * hp) + 0)  # ponteiro das horas ~ 13h30
    if hp > 0:
        line(d, [(cx, cy), (cx + 120 * math.cos(hm), cy + 120 * math.sin(hm))], ROSA, 4.5, a)
        line(d, [(cx, cy), (cx + 80 * math.cos(hh), cy + 80 * math.sin(hh))], ROSA, 6, a)
        d.ellipse(((cx - 8) * S, (cy - 8) * S, (cx + 8) * S, (cy + 8) * S), fill=ROSA + (int(255 * a),))
    ah = scene_alpha(t, T["horario"], t_out)
    if ah > 0:
        spaced(d, 540, 1035, "É SÓ VIR NO HORÁRIO DA LOJA", 30, CINZA, ah, 0.18, "inter6")
        text_parts(d, 1130, [("Seg a Sex · ", False), ("13h30 às 17h30", True)], 64, ah, fonts=("pf6", "pf6i"))


def bag_shape():
    o = lambda pts: [(540 + (x - 540), y) for x, y in pts]
    return dict(
        hook=[quad((528, 652), (540, 630), (552, 648), 10), [(552, 648), (540, 676)]],
        bag=[[(540, 676), (430, 720), (410, 740), (410, 1230), (670, 1230), (670, 740), (650, 720), (540, 676)]],
        zip=[(540, 700), (540, 1210)],
    )


def scene_p4(d, gd, t):
    t0, t_out = T["p4_in"], T["p4_out"]
    if t < t0 - 0.05 or t > t_out + 0.35:
        return
    pill(d, t, t0, t_out, "PASSO 4 · DEVOLUÇÃO")
    a = scene_alpha(t, t0, t_out)
    text_parts(d, 420, [("Depois da ", False), ("festa", True)], 84, a)
    a_out = 1 - ease(prog(t, t_out, 0.3))
    xrow(d, t, T["lavar"], 545, "Não precisa lavar", a_out, x=290)
    xrow(d, t, T["passar"], 625, "Não precisa passar", a_out, x=290)
    sh = bag_shape()
    pb = ease(prog(t, T["capinha"] - 0.3, 0.9))
    if pb > 0:
        for pts in sh["hook"] + sh["bag"]:
            line(d, partial(pts, pb), BRANCO, 3.2, 0.92 * a_out)
        pz = ease(prog(t, T["capinha"] + 0.5, 1.2))
        if pz > 0:
            zz = partial(sh["zip"], pz)
            line(d, zz, ROSA, 4, a_out)
            line(gd, zz, ROSA, 12, 0.8 * a_out)
            zx, zy = zz[-1]
            d.rounded_rectangle(((zx - 9) * S, (zy - 4) * S, (zx + 9) * S, (zy + 22) * S), 5 * S, fill=ROSA + (int(255 * a_out),))
        line(d, [(470, 770), (610, 770)], BRANCO, 2, 0.35 * a_out * pb)
    at = scene_alpha(t, T["trazer"], t_out)
    if at > 0:
        text_parts(d, 1380, [("É só trazer pra ", False), ("loja", True)], 72, at)


def scene_final(base, t):
    t0 = T["final"]
    if t < t0:
        return
    p = ease(prog(t, t0, 0.4))
    cx0, cy0, cx1, cy1 = 140, 640, 940, 1280
    dy = int(40 * (1 - p))
    card, cd = layer()
    cd.rounded_rectangle((cx0 * S, (cy0 + dy) * S, cx1 * S, (cy1 + dy) * S), 28 * S, fill=(20, 20, 20, 245))
    lw = 520
    lg = A.LOGO_IM.resize((lw * S, int(A.LOGO_IM.height * lw / A.LOGO_IM.width) * S), Image.LANCZOS)
    card.alpha_composite(lg, ((W * S - lg.width) // 2, (cy0 + 60 + dy) * S))
    yl = cy0 + 60 + lg.height // S + 40 + dy
    line(cd, [(cx0 + 60, yl), (cx1 - 60, yl)], ROSA, 2)
    line(cd, [(cx0 + 60, cy1 - 50 + dy), (cx1 - 60, cy1 - 50 + dy)], ROSA, 2)
    text_parts(cd, cy0 + 315 + dy, [("Visite ", False), ("nossa loja", True)], 78)
    f = font("mont", 36)
    cd.text((540 * S, (cy0 + 410 + dy) * S), "Seg a Sex · 13h30 às 17h30", font=f, fill=(235, 230, 228, 255), anchor="mm")
    cd.text((540 * S, (cy0 + 465 + dy) * S), "Cristalina – GO", font=f, fill=(190, 180, 178, 255), anchor="mm")
    cd.text((540 * S, (cy1 - 105 + dy) * S), "@flordelotusvestidos", font=font("mont7", 34), fill=ROSA + (255,), anchor="mm")
    if p < 1:
        card.putalpha(card.split()[3].point(lambda v: int(v * p)))
    base.alpha_composite(card)


def frame(i):
    t = i / FPS
    base, d = layer()
    gl, gd = layer()
    hk = scene_hook(t)
    if hk is not None:
        base.alpha_composite(hk)
    scene_garments(d, gd, t)
    scene_stamp(d, base, t)
    scene_p1(d, base, t)
    scene_dica(d, gd, t)
    scene_p2(d, t)
    scene_p3(d, t)
    scene_p4(d, gd, t)
    scene_final(base, t)
    small = base.resize((W, H), Image.LANCZOS)
    glow = gl.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(12))
    glow.putalpha(glow.split()[3].point(lambda v: int(v * 0.55)))
    out = A.BG.copy()
    out.alpha_composite(glow)
    out.alpha_composite(small)
    return out.convert("RGB").tobytes()


def main():
    out = sys.argv[1]
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else DUR
    first = int(float(sys.argv[3]) * FPS) if len(sys.argv) > 3 else 0
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    with Pool(4, initializer=A.init) as pool:
        for buf in pool.imap(frame, range(first, int(dur * FPS)), chunksize=4):
            ff.stdin.write(buf)
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    main()
