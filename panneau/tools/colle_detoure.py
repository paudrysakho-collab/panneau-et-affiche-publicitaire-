"""Colle un produit détouré (PNG transparent) par-dessus une photo, à une position et une échelle données.

Sert à remplacer un produit dont l'IA a changé la forme : le vrai produit détouré, un peu plus large que
l'ancien, le recouvre entièrement.

Usage (depuis panneau/) :
    python3 tools/colle_detoure.py entree.jpg sortie.jpg produit.png X0 Y0 ECHELLE
    (X0, Y0 : coin haut gauche du PNG une fois mis à l'échelle)
"""
import sys

import numpy as np
from PIL import Image


def main():
    entree, sortie, produit = sys.argv[1:4]
    x0, y0, k = int(sys.argv[4]), int(sys.argv[5]), float(sys.argv[6])
    img = Image.open(entree).convert('RGB')
    p = Image.open(produit).convert('RGBA')
    p = p.resize((round(p.width * k), round(p.height * k)), Image.LANCZOS)
    a = np.array(p).astype(np.float32)
    rgb, alpha = a[..., :3], a[..., 3:] / 255
    out = np.array(img).astype(np.float32)
    h, w = rgb.shape[:2]
    zone = out[y0:y0 + h, x0:x0 + w]
    out[y0:y0 + h, x0:x0 + w] = zone * (1 - alpha) + rgb * alpha
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(sortie, quality=95)
    print(sortie)


if __name__ == '__main__':
    main()
