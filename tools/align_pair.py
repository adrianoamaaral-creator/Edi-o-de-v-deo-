"""Alinha a foto ANTES à foto DEPOIS por pontos de referência (transformação afim por mínimos quadrados)
e recorta as duas com os lábios no centro, boca na horizontal.
Uso: align_pair.py antes.png depois.png saida_antes.png saida_depois.png"""
import sys, math, cv2, numpy as np
A, D, OA, OD = sys.argv[1:5]
# pontos (x,y) nas fotos já em pé: canto esq. da boca, canto dir., centro da linha da boca, base do lábio inferior, piercing do nariz
PA = np.float32([(520, 311), (724, 424), (625, 365), (610, 415), (590, 160)])
PD = np.float32([(535, 380), (812, 432), (675, 387), (675, 457), (612, 207)])
OW, OH, MOUTH = 1160, 892, 560          # tamanho do recorte e largura final da boca (px)
a = cv2.imread(A); d = cv2.imread(D)
M, _ = cv2.estimateAffine2D(PA, PD, method=cv2.LMEDS)       # antes -> espaço do depois
# nivelamento + escala + centralização no espaço do depois
(lx, ly), (rx, ry) = PD[0], PD[1]
ang = math.degrees(math.atan2(ry - ly, rx - lx)); k = MOUTH / math.hypot(rx - lx, ry - ly)
cx, cy = PD[2]                                        # centro dos lábios
R = cv2.getRotationMatrix2D((float(cx), float(cy)), ang, k)
R[0, 2] += OW / 2 - cx; R[1, 2] += OH / 2 - cy
def compose(B, C):  # aplica C depois de B
    B3 = np.vstack([B, [0, 0, 1]]); C3 = np.vstack([C, [0, 0, 1]]); return (C3 @ B3)[:2]
cv2.imwrite(OD, cv2.warpAffine(d, R, (OW, OH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT))
cv2.imwrite(OA, cv2.warpAffine(a, compose(M, R), (OW, OH), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT))
res = cv2.transform(PA[None], M)[0] - PD
print("erro médio do alinhamento (px):", float(np.linalg.norm(res, axis=1).mean()))
