"""Prolonge le bas d'une photo studio (surface brillante) quand les produits touchent le bord.

Les N lignes ajoutées sont le reflet miroir des N dernières lignes, qui s'assombrit et se fond
progressivement dans la couleur de la surface : les pots gardent un reflet au lieu d'être coupés net.

Usage (depuis panneau/) :
    python3 tools/etend_bas.py entree.jpg sortie.jpg N
"""
import sys

import cv2
import numpy as np
from PIL import Image


def main():
    entree, sortie, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    img = np.array(Image.open(entree).convert('RGB')).astype(np.float32)[:-3]  # dernières lignes souvent plus claires
    miroir = img[-n:][::-1].copy()
    miroir = cv2.GaussianBlur(miroir, (0, 0), 2.5)
    # couleur de la surface : médiane de la dernière ligne, lissée horizontalement
    surface = cv2.GaussianBlur(np.median(img[-4:], axis=0, keepdims=True), (0, 0), sigmaX=40, sigmaY=0.1)
    surface = np.repeat(surface, n, axis=0)
    t = np.linspace(0, 1, n, dtype=np.float32)[:, None, None]
    reflet = 0.55 * (1 - t) ** 1.5  # part du reflet, qui s'efface en descendant
    ext = (miroir * reflet + surface * (1 - reflet)) * (1 - 0.25 * t)
    ext += np.random.default_rng(2).normal(0, 1.0, ext.shape).astype(np.float32)
    out = np.vstack([img, ext])
    # raccord adouci sur quelques lignes
    H = img.shape[0]
    bande = out[H - 5:H + 5]
    out[H - 5:H + 5] = cv2.GaussianBlur(bande, (0, 0), sigmaX=0.1, sigmaY=1.6)
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(sortie, quality=95)
    print(sortie, out.shape[1], 'x', out.shape[0])


if __name__ == '__main__':
    main()
