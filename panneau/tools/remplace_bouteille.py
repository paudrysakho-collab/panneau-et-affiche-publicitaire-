"""Remplace une bouteille de la photo IA (forme fausse) par la vraie bouteille détourée d'une photo du produit.

1. Les parties de l'ancienne bouteille qui dépasseront de la nouvelle (col, épaules) sont effacées : le mur
   derrière est reconstruit par inpainting dans un polygone.
2. La vraie bouteille (PNG détouré) est mise à l'échelle sur la largeur du corps de l'ancienne et posée au
   même endroit (même centre, même bas).
3. Étalonnage : le verre prend les couleurs du verre de la scène (moyenne et écart-type par canal, sur une
   zone de référence de la scène) ; l'étiquette garde ses couleurs, seulement ramenée à la luminosité de
   l'étiquette de la scène.

Usage (depuis panneau/) :
    python3 tools/remplace_bouteille.py scene.jpg sortie.jpg bouteille.png CX BAS LARGEUR_CORPS \\
        --efface x,y x,y ...                 (polygone de l'ancienne bouteille à effacer)
        --verre-scene X0 Y0 X1 Y1            (zone de verre de l'ancienne bouteille, pour l'étalonnage)
        --etiquette-png CX CY RX RY          (ellipse de l'étiquette dans le PNG, en pixels du PNG)
        --etiquette-scene X0 Y0 X1 Y1        (zone d'étiquette dans la scène, pour la luminosité)
"""
import argparse

import cv2
import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scene')
    ap.add_argument('sortie')
    ap.add_argument('bouteille')
    ap.add_argument('cx', type=float)
    ap.add_argument('bas', type=float)
    ap.add_argument('largeur', type=float)
    ap.add_argument('--efface', nargs='+', default=[])
    ap.add_argument('--verre-scene', type=int, nargs=4, required=True)
    ap.add_argument('--etiquette-png', type=float, nargs=4, required=True)
    ap.add_argument('--etiquette-scene', type=int, nargs=4, required=True)
    a = ap.parse_args()

    img = np.array(Image.open(a.scene).convert('RGB'))
    H, W = img.shape[:2]

    # 1. effacement de l'ancienne forme
    if a.efface:
        poly = np.array([list(map(int, p.split(','))) for p in a.efface], np.int32)
        z = np.zeros((H, W), np.uint8)
        cv2.fillPoly(z, [poly], 255)
        fond = cv2.inpaint(img, z, 15, cv2.INPAINT_TELEA)
        lisse = cv2.GaussianBlur(fond, (0, 0), 4)
        img = np.where(z[..., None] > 0, lisse, img)

    # 2. vraie bouteille
    p = np.array(Image.open(a.bouteille).convert('RGBA')).astype(np.float32)
    al = p[..., 3] / 255
    al = cv2.erode(al, np.ones((3, 3), np.uint8))          # pas de liseré du fond de la photo
    ys = np.where((al > 0.5).any(axis=1))[0]
    larg = [(al[y] > 0.5).sum() for y in ys]
    n = len(ys)
    corps = np.median(larg[int(n * 0.45):int(n * 0.75)])
    k = a.largeur / corps
    rgb = p[..., :3]

    # 3. étalonnage
    ecx, ecy, erx, ery = a.etiquette_png
    yy, xx = np.mgrid[0:p.shape[0], 0:p.shape[1]]
    etiq = (((xx - ecx) / erx) ** 2 + ((yy - ecy) / ery) ** 2) <= 1
    verre = (al > 0.5) & ~etiq
    X0, Y0, X1, Y1 = a.verre_scene
    sc = img[Y0:Y1, X0:X1].reshape(-1, 3).astype(np.float32)
    src = rgb[verre]
    m_s, s_s = src.mean(0), src.std(0) + 1e-3
    m_c, s_c = sc.mean(0), sc.std(0) + 1e-3
    rgb_v = (rgb - m_s) / s_s * s_c + m_c
    X0, Y0, X1, Y1 = a.etiquette_scene
    lab_sc = img[Y0:Y1, X0:X1].reshape(-1, 3).astype(np.float32).mean(0)
    lab_src = rgb[etiq & (al > 0.5)].mean(0)
    rgb_e = rgb * (lab_sc / np.maximum(lab_src, 1))
    t = cv2.GaussianBlur(etiq.astype(np.float32), (0, 0), 1.5)[..., None]   # bord d'étiquette fondu
    rgb = rgb_v * (1 - t) + rgb_e * t

    # 4. mise à l'échelle et pose (centre et bas alignés)
    w2, h2 = round(p.shape[1] * k), round(p.shape[0] * k)
    rgb = cv2.resize(rgb.clip(0, 255), (w2, h2), interpolation=cv2.INTER_AREA)
    al = cv2.resize(al, (w2, h2), interpolation=cv2.INTER_AREA)
    bas_png = ys[-1] * k
    cx_png = np.median(np.where(al[int(h2 * 0.6)] > 0.5)[0])
    x0 = int(round(a.cx - cx_png))
    y0 = int(round(a.bas - bas_png))
    out = img.astype(np.float32)
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(W, x0 + w2), min(H, y0 + h2)
    A = al[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
    out[ya:yb, xa:xb] = out[ya:yb, xa:xb] * (1 - A) + rgb[ya - y0:yb - y0, xa - x0:xb - x0] * A
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(a.sortie, quality=95)
    print(a.sortie, 'échelle', round(k, 3), 'haut', y0 + int(ys[0] * k), 'gauche', x0)


if __name__ == '__main__':
    main()
