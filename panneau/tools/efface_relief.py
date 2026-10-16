"""Efface un motif en relief inventé sur le verre d'une bouteille (blason, texte gravé) : le verre redevient lisse.

Dans un polygone qui suit l'intérieur de la bouteille, chaque pixel est remplacé par la médiane d'une
fenêtre haute et étroite : les fins traits du relief disparaissent, les longs reflets verticaux du verre
restent. Bords du polygone fondus, grain léger rajouté.

Usage (depuis panneau/) :
    python3 tools/efface_relief.py entree.jpg sortie.jpg x1,y1 x2,y2 x3,y3 ...   (polygone, au moins 3 points)
"""
import sys

import cv2
import numpy as np
from PIL import Image
from scipy.ndimage import median_filter


def main():
    entree, sortie = sys.argv[1], sys.argv[2]
    poly = np.array([list(map(int, p.split(','))) for p in sys.argv[3:]], np.int32)
    img = np.array(Image.open(entree).convert('RGB'))
    H, W = img.shape[:2]
    dedans = np.zeros((H, W), np.uint8)
    cv2.fillPoly(dedans, [poly], 255)

    x0, y0, w, h = cv2.boundingRect(poly)
    m = 20
    X0, Y0, X1, Y1 = max(0, x0 - m), max(0, y0 - m), min(W, x0 + w + m), min(H, y0 + h + m)
    zone = img[Y0:Y1, X0:X1].astype(np.float32)
    lisse = np.stack([median_filter(zone[..., c], size=(31, 9)) for c in range(3)], axis=-1)
    lisse = cv2.GaussianBlur(lisse, (0, 0), sigmaX=1.0, sigmaY=3.0)
    lisse += np.random.default_rng(3).normal(0, 1.2, lisse.shape).astype(np.float32)
    a = cv2.GaussianBlur(dedans[Y0:Y1, X0:X1].astype(np.float32) / 255, (0, 0), 2.5)[..., None]
    out = img.copy()
    out[Y0:Y1, X0:X1] = (zone * (1 - a) + lisse * a).clip(0, 255).astype(np.uint8)
    Image.fromarray(out).save(sortie, quality=95)
    print(sortie)


if __name__ == '__main__':
    main()
