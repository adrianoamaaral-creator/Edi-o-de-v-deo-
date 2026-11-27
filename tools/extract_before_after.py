"""Extrai as fotos de antes/depois do vídeo (média de quadros + remoção do ícone/@ do Instagram por inpainting).
Uso: extract_before_after.py DIR_QUADROS OUT_DIR"""
import sys, glob, cv2, numpy as np
D, O = sys.argv[1], sys.argv[2]
def avg(prefix):
    fs = sorted(glob.glob(f"{D}/{prefix}*.png")); return np.mean([cv2.imread(f).astype(np.float32) for f in fs], 0).astype(np.uint8)
def trim(im):
    g = im.sum(2); ys = np.where((g > 150).mean(1) > 0.6)[0]; xs = np.where((g > 150).mean(0) > 0.6)[0]
    return im
b = avg("b"); a = avg("a")
# máscara do ícone/@: pixels quase brancos (pouca saturação, muito claros) + dilatação
hsv = cv2.cvtColor(a, cv2.COLOR_BGR2HSV)
mask = ((hsv[..., 2] > 200) & (hsv[..., 1] < 60)).astype(np.uint8) * 255
mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=2)
a_clean = cv2.inpaint(a, mask, 6, cv2.INPAINT_TELEA)
cv2.imwrite(f"{O}/antes_raw.png", b); cv2.imwrite(f"{O}/depois_raw.png", a); cv2.imwrite(f"{O}/depois_mask.png", mask); cv2.imwrite(f"{O}/depois_clean.png", a_clean)
