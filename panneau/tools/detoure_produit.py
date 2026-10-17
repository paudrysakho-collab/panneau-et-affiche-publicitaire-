"""Détoure un produit (BiRefNet) et enregistre un PNG transparent recadré au plus juste.

Usage (depuis panneau/) :
    python3 tools/detoure_produit.py source.jpg sortie.png [--fond-blanc]
      --fond-blanc : la source est déjà détourée sur fond blanc uni (Tomatin, Silure) :
                     l'alpha vient de l'écart au blanc, plus fin que le réseau sur ces bords.
"""
import sys

import cv2
import numpy as np
from PIL import Image


def main():
    src, sortie = sys.argv[1:3]
    im = Image.open(src).convert('RGB')
    a = None
    if '--fond-blanc' in sys.argv:
        f = np.array(im).astype(np.float32)
        ecart = (255 - f.min(axis=2))
        a = np.clip((ecart - 4) / 18, 0, 1)
        # remplit l'intérieur (verre très clair, reflets blancs) : composante pleine
        m = (a > 0.5).astype(np.uint8)
        cont, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        plein = np.zeros_like(m)
        cv2.drawContours(plein, [max(cont, key=cv2.contourArea)], -1, 1, -1)
        a = np.maximum(a, cv2.GaussianBlur(plein.astype(np.float32), (0, 0), 0.8)) * cv2.dilate(plein, np.ones((5, 5), np.uint8))
    else:
        from rembg import new_session, remove
        a = np.array(remove(im, session=new_session('birefnet-general')))[..., 3].astype(np.float32) / 255
        # garde la plus grande composante (le produit), retire les miettes du décor
        m = (a > 0.5).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        if n > 2:
            k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
            garde = cv2.dilate((lab == k).astype(np.uint8), np.ones((9, 9), np.uint8))
            a *= garde
    ys, xs = np.where(a > 0.02)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rgba = np.dstack([np.array(im), (a * 255).astype(np.uint8)])[y0:y1, x0:x1]
    Image.fromarray(rgba, 'RGBA').save(sortie)
    print(sortie, rgba.shape[1], 'x', rgba.shape[0])


if __name__ == '__main__':
    main()
