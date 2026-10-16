"""Déplace horizontalement un objet posé devant un fond sombre et uni (ex. le sachet de chocolats).

La boîte de l'objet est d'abord remplacée par un fond reconstitué (dégradé ligne par ligne entre le
fond à gauche et à droite de la boîte), puis le bloc d'origine est recollé décalé de dx pixels, bords
haut et côtés fondus. Convient quand le fond est sombre et uni et que la boîte laisse une marge autour
de l'objet.

Usage (depuis panneau/) :
    python3 tools/deplace_objet.py entree.jpg sortie.jpg x0 y0 x1 y1 dx
"""
import sys

import cv2
import numpy as np
from PIL import Image


def main():
    src, dst = sys.argv[1], sys.argv[2]
    x0, y0, x1, y1, dx = map(int, sys.argv[3:8])
    img = np.array(Image.open(src).convert('RGB')).astype(np.float32)
    H, W = img.shape[:2]
    out = img.copy()

    # 1. plaque de fond sans l'objet : pour chaque ligne, dégradé entre le fond à gauche et à droite
    #    de la boîte, plus le grain de l'image
    g = img[y0:y1, max(0, x0 - 12):x0].mean(axis=1)
    d = img[y0:y1, x1:min(W, x1 + 12)].mean(axis=1)
    u = np.linspace(0, 1, x1 - x0, dtype=np.float32)[None, :, None]
    plaque = g[:, None, :] * (1 - u) + d[:, None, :] * u
    plaque = cv2.GaussianBlur(plaque, (0, 0), 3)
    rng = np.random.default_rng(0)
    plaque += rng.normal(0, 1.2, plaque.shape).astype(np.float32)
    out[y0:y1, x0:x1] = plaque

    # 2. bloc de l'objet (avec son fond, sombre et uni) recollé décalé, bords fondus
    bloc = img[y0:y1, x0:x1]
    h, w = bloc.shape[:2]
    f = 14
    a = np.ones((h, w), np.float32)
    rampe = np.linspace(0, 1, f, dtype=np.float32)
    a[:, :f] *= rampe
    a[:, -f:] *= rampe[::-1]
    a[:f, :] *= rampe[:, None]
    a = a[..., None]
    nx0 = x0 + dx
    cible = out[y0:y1, nx0:nx0 + w]
    out[y0:y1, nx0:nx0 + w] = cible * (1 - a) + bloc * a

    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(dst, quality=95)
    print(dst)


if __name__ == '__main__':
    main()
