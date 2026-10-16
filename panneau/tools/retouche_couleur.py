"""Corrige la couleur d'un liquide ou d'un contenu que l'IA a mal teinté, dans un polygone.

    teinte  : décale la teinte (et peut renforcer la saturation) des pixels colorés du polygone
              (ex. rhum rosé -> rhum doré) ; le verre clair, les reflets blancs et le fond ne bougent pas.
    couleur : remplace la couleur par une couleur cible en gardant la texture (luminosité relative)
              (ex. tartinable beige -> purée vert foncé).

Usage (depuis panneau/) :
    python3 tools/retouche_couleur.py entree.jpg sortie.jpg teinte DECALAGE SAT_MIN x,y x,y ...
        DECALAGE : en tours de roue (0.06 = 22°), SAT_MIN : saturation mini des pixels touchés (0..1)
    python3 tools/retouche_couleur.py entree.jpg sortie.jpg couleur R G B x,y x,y ...
    python3 tools/retouche_couleur.py entree.jpg sortie.jpg lisse SX SY x,y x,y ...
        (flou directionnel : efface une texture inventée, ex. motif sur une bague de capsule)
"""
import sys

import cv2
import numpy as np
from PIL import Image


def main():
    entree, sortie, mode = sys.argv[1:4]
    img = np.array(Image.open(entree).convert('RGB'))
    H, W = img.shape[:2]
    if mode == 'teinte':
        dec, smin = float(sys.argv[4]), float(sys.argv[5])
        pts = sys.argv[6:]
    elif mode == 'lisse':
        sx, sy = float(sys.argv[4]), float(sys.argv[5])
        pts = sys.argv[6:]
    else:
        cible = np.array(list(map(float, sys.argv[4:7])), np.float32)
        pts = sys.argv[7:]
    poly = np.array([list(map(int, p.split(','))) for p in pts], np.int32)
    z = np.zeros((H, W), np.uint8)
    cv2.fillPoly(z, [poly], 255)
    a = cv2.GaussianBlur(z.astype(np.float32) / 255, (0, 0), 1.0 if mode == 'lisse' else 2.5)

    if mode == 'teinte':
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV_FULL).astype(np.float32)  # teinte 0..255
        h, s = hsv[..., 0], hsv[..., 1] / 255
        poids = np.clip((s - smin) / 0.15, 0, 1)                            # fondu sur la saturation
        hsv[..., 0] = (h + dec * 256 * poids) % 256
        neuf = cv2.cvtColor(hsv.clip(0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB_FULL).astype(np.float32)
    elif mode == 'lisse':
        neuf = cv2.GaussianBlur(img.astype(np.float32), (0, 0), sigmaX=sx, sigmaY=sy)
    else:
        f = img.astype(np.float32)
        L = f @ np.array([0.299, 0.587, 0.114], np.float32)
        Lm = L[z > 0].mean()
        neuf = (cible[None, None, :] * (L / max(Lm, 1))[..., None] ** 0.8)
    out = img.astype(np.float32) * (1 - a[..., None]) + neuf * a[..., None]
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(sortie, quality=95)
    print(sortie)


if __name__ == '__main__':
    main()
