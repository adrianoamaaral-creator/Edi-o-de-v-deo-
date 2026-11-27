"""Remove os textos sobrepostos da foto do post Hidragloss (inpainting) e recorta a área dos lábios.
Uso: clean_hidragloss.py post.jpg saida.png"""
import sys, cv2, numpy as np
im = cv2.imread(sys.argv[1]); H, W = im.shape[:2]
boxes = [(460, 530, 710, 645), (160, 695, 345, 775), (795, 675, 1060, 795), (90, 890, 385, 1005), (865, 960, 1095, 1040), (480, 1185, 690, 1265)]
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY); mask = np.zeros_like(g)
for x0, y0, x1, y1 in boxes:
    sub = g[y0:y1, x0:x1]; mask[y0:y1, x0:x1] = (sub < 120).astype(np.uint8) * 255
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=3)
out = cv2.inpaint(im, mask, 9, cv2.INPAINT_TELEA)
# suaviza só dentro das áreas tratadas para esconder o "remendo"
blur = cv2.GaussianBlur(out, (0, 0), 3); m3 = cv2.GaussianBlur(mask, (0, 0), 6)[..., None] / 255.0
out = (out * (1 - m3 * 0.6) + blur * (m3 * 0.6)).astype(np.uint8)
cv2.imwrite(sys.argv[2], out[620:H, 0:W])
