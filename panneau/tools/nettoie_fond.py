"""Efface un élément parasite du fond (ex. un projecteur de studio ajouté par l'IA) en recalculant le dégradé.

Le fond autour (hors produits) est modélisé par une surface lisse (polynôme de degré 3 par canal, ajusté
dans une zone de travail). Les pixels trop clairs par rapport à ce modèle, dans la zone, sont remplacés
par le modèle (+ un grain léger), avec un fondu. Les produits ne sont jamais touchés (masques visibles de
la maquette, élargis).

Usage (depuis panneau/) :
    python3 tools/nettoie_fond.py photo.png sortie.png X0 Y0 X1 Y1 --visibles studio/groupe [--seuil 10]
"""
import argparse
import glob

import cv2
import numpy as np
from PIL import Image


def base_poly(x, y):
    return np.stack([np.ones_like(x), x, y, x * x, x * y, y * y, x ** 3, x * x * y, x * y * y, y ** 3], -1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('photo')
    ap.add_argument('sortie')
    ap.add_argument('boite', nargs=4, type=int)
    ap.add_argument('--visibles', required=True)
    ap.add_argument('--seuil', type=float, default=10)
    a = ap.parse_args()
    im = np.array(Image.open(a.photo).convert('RGB')).astype(np.float32)
    H, W = im.shape[:2]
    prod = np.zeros((H, W), np.uint8)
    for f in glob.glob(f'{a.visibles}/visible_*.png'):
        prod |= (np.array(Image.open(f)) > 127).astype(np.uint8)
    prod = cv2.dilate(prod, np.ones((61, 61), np.uint8))           # marge : les produits ont pu bouger un peu
    x0, y0, x1, y1 = a.boite
    # zone de travail élargie pour l'ajustement du dégradé
    ex0, ey0, ex1, ey1 = max(0, x0 - 300), max(0, y0 - 300), min(W, x1 + 500), min(H, y1 + 400)
    yy, xx = np.mgrid[ey0:ey1, ex0:ex1].astype(np.float32)
    nx, ny = xx / W, yy / H
    zone = im[ey0:ey1, ex0:ex1]
    libre = prod[ey0:ey1, ex0:ex1] == 0
    A = base_poly(nx, ny)
    # 1er ajustement hors de la boîte suspecte, puis on exclut tout ce qui dépasse
    dedans = np.zeros_like(libre)
    dedans[y0 - ey0:y1 - ey0, x0 - ex0:x1 - ex0] = True
    pts = libre & ~dedans
    modele = np.zeros_like(zone)
    for c in range(3):
        coef, *_ = np.linalg.lstsq(A[pts], zone[..., c][pts], rcond=None)
        modele[..., c] = A @ coef
    ecart = (zone - modele).mean(2)
    parasite = (ecart > a.seuil) & dedans & libre
    parasite = cv2.dilate(parasite.astype(np.uint8), np.ones((25, 25), np.uint8)) & libre & dedans
    m = cv2.GaussianBlur(parasite.astype(np.float32), (0, 0), 12)
    m = np.clip(m * 1.6, 0, 1) * libre * dedans
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3)
    grain = np.random.default_rng(1).normal(0, 1.2, zone.shape).astype(np.float32)
    zone[:] = zone * (1 - m[..., None]) + (modele + grain) * m[..., None]
    Image.fromarray(np.clip(im, 0, 255).round().astype(np.uint8)).save(a.sortie)
    print(f'{int(parasite.sum())} px de parasite remplacés')


if __name__ == '__main__':
    main()
