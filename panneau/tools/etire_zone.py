"""Rééchantillonne verticalement une bande de la photo par morceaux : sert à rendre une partie plus haute
qu'une autre sans rien inventer (ex. couvercle de pot trop plat : le couvercle s'allonge, le col raccourcit).

Usage (depuis panneau/) :
    python3 tools/etire_zone.py entree.jpg sortie.jpg X0 X1 A0:N0 A1:N1 A2:N2 ...
    Les lignes d'origine A0 < A1 < ... sont envoyées sur les lignes N0 < N1 < ... (interpolation linéaire
    entre deux repères), entre les colonnes X0 et X1. Les repères extrêmes doivent rester en place.
"""
import sys

import cv2
import numpy as np
from PIL import Image

entree, sortie = sys.argv[1], sys.argv[2]
x0, x1 = int(sys.argv[3]), int(sys.argv[4])
rep = [tuple(map(float, r.split(':'))) for r in sys.argv[5:]]
img = np.array(Image.open(entree).convert('RGB'))
H, W = img.shape[:2]
anc = [r[0] for r in rep]
neu = [r[1] for r in rep]
y_a, y_b = int(neu[0]), int(neu[-1])
mapy = np.zeros((y_b - y_a + 1, x1 - x0), np.float32)
mapx = np.tile(np.arange(x0, x1, dtype=np.float32), (y_b - y_a + 1, 1))
for i, y in enumerate(range(y_a, y_b + 1)):
    mapy[i, :] = np.interp(y, neu, anc)
bande = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)
out = img.copy()
# bords gauche/droite fondus sur 2 px
a = np.ones((1, x1 - x0, 1), np.float32)
a[0, :2, 0] = [0.33, 0.66]
a[0, -2:, 0] = [0.66, 0.33]
out[y_a:y_b + 1, x0:x1] = (img[y_a:y_b + 1, x0:x1] * (1 - a) + bande * a).astype(np.uint8)
Image.fromarray(out).save(sortie, quality=95)
print(sortie)
