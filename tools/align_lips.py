"""Endireita e recorta fotos de lábios centradas na boca.
Uso: align_lips.py foto_em_pe.png cantoE_x cantoE_y cantoD_x cantoD_y largura_alvo_boca saida.png [W H]"""
import sys, math
from PIL import Image
src, lx, ly, rx, ry, target, out = sys.argv[1], *map(float, sys.argv[2:7]), sys.argv[7]
OW, OH = (int(sys.argv[8]), int(sys.argv[9])) if len(sys.argv) > 9 else (1160, 892)
im = Image.open(src).convert("RGB")
cx, cy = (lx + rx) / 2, (ly + ry) / 2
ang = math.degrees(math.atan2(ry - ly, rx - lx)); width = math.hypot(rx - lx, ry - ly)
k = target / width
im = im.rotate(ang, resample=Image.BICUBIC, center=(cx, cy), expand=False)   # deixa a boca na horizontal
im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS); cx, cy = cx * k, cy * k
box = (round(cx - OW / 2), round(cy - OH / 2 + OH * 0.04), round(cx + OW / 2), round(cy + OH / 2 + OH * 0.04))
im.crop(box).save(out); print(out, "ang", round(ang, 1), "escala", round(k, 2))
