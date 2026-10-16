"""Reprend un motif imprimé clair (blason, ornement) sur la photo du vrai produit et le peint à la place du
motif inventé par l'IA, sans emporter le fond de la photo source.

1. Zone cible : le motif clair de l'IA est effacé (fond estimé par ouverture morphologique, fondu).
2. Zone source : le motif est extrait en niveaux (clair sur fond plus sombre) -> masque alpha.
3. Le masque, mis à la taille de la cible, est peint dans la couleur donnée.

Usage (depuis panneau/) :
    python3 tools/motif_photo.py entree.jpg sortie.jpg source.jpg SX0 SY0 SX1 SY1 DX0 DY0 DX1 DY1 R G B [SEUIL]
"""
import sys

import cv2
import numpy as np
from PIL import Image


def main():
    entree, sortie, source = sys.argv[1:4]
    sx0, sy0, sx1, sy1, dx0, dy0, dx1, dy1 = map(int, sys.argv[4:12])
    couleur = np.array(list(map(float, sys.argv[12:15])), np.float32)
    seuil = float(sys.argv[15]) if len(sys.argv) > 15 else 0.25
    img = np.array(Image.open(entree).convert('RGB')).astype(np.float32)
    src = np.array(Image.open(source).convert('RGB')).astype(np.float32)[sy0:sy1, sx0:sx1]

    # 1. effacement du motif de l'IA (pixels clairs) dans la cible
    m = 3
    Y0, Y1, X0, X1 = dy0 - m, dy1 + m, dx0 - m, dx1 + m
    reg = img[Y0:Y1, X0:X1]
    k = max(5, int(min(dy1 - dy0, dx1 - dx0) * 0.6)) | 1
    fond = cv2.morphologyEx(reg, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    fond = cv2.GaussianBlur(fond, (0, 0), 2)
    a = np.zeros(reg.shape[:2], np.float32)
    a[m:-m, m:-m] = 1
    a = cv2.GaussianBlur(a, (0, 0), 1.2)[..., None]
    img[Y0:Y1, X0:X1] = reg * (1 - a) + fond * a

    # 2. masque du motif dans la source : clair par rapport à son fond local
    L = src @ np.array([0.299, 0.587, 0.114], np.float32)
    ks = max(5, int(min(L.shape) * 0.6)) | 1
    fl = cv2.morphologyEx(L, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks)))
    d = L - cv2.GaussianBlur(fl, (0, 0), 2)
    haut = np.percentile(d, 99)
    alpha = np.clip((d / max(haut, 1) - seuil) / (1 - seuil), 0, 1)

    # 3. peinture du motif à la taille de la cible
    alpha = cv2.resize(alpha, (dx1 - dx0, dy1 - dy0), interpolation=cv2.INTER_AREA)[..., None]
    zone = img[dy0:dy1, dx0:dx1]
    img[dy0:dy1, dx0:dx1] = zone * (1 - alpha) + couleur * alpha
    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(sortie, quality=95)
    print(sortie)


if __name__ == '__main__':
    main()
