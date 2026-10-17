"""Remplace une étiquette redessinée par l'IA par la vraie étiquette, prise sur la photo d'origine.

L'étiquette source est mise à la largeur de l'étiquette cible ; si les proportions diffèrent, le
papier est prolongé en haut et en bas. L'éclairage de la photo IA (dégradés, ombre du côté droit,
couleur) est conservé : on transfère sa composante basse fréquence sur la vraie étiquette.

Usage (depuis panneau/) :
    python3 tools/remplace_etiquette.py photo.jpg sortie.jpg source.jpg SX0 SY0 SX1 SY1 DX0 DY0 DX1 DY1 [CX0 CY0 CX1 CY1 ...]
    Les rectangles C… (facultatifs, coordonnées de la photo) sont les parties de l'étiquette cachées par un
    autre produit placé devant : on n'y touche pas.
    Variable OVALE=1 : étiquette ovale (masque elliptique inscrit dans la boîte, source étirée à la boîte).
    Variable CACHE_POLY="x,y x,y ...;..." : parties cachées données en polygones (bords lisses).
    Variable GAIN=r,g,b : étiquette posée sur du verre nu (pas de transfert d'éclairage, gain par canal).
    Variable FONDU=n : bords fondus sur n px (3 par défaut).
    Variable ETIRER=1 : source étirée à la boîte (proportions proches), sans prolongement du papier.
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image


def basse_frequence(a, sigma):
    """Éclairage d'une étiquette sans son texte : médiane (efface les lettres) puis flou."""
    m = cv2.medianBlur(a.astype(np.uint8), 31).astype(np.float32)
    return cv2.GaussianBlur(m, (0, 0), sigma)


def main():
    photo, sortie, source = sys.argv[1:4]
    sx0, sy0, sx1, sy1, dx0, dy0, dx1, dy1 = map(int, sys.argv[4:12])
    caches = list(map(int, sys.argv[12:]))
    img = np.array(Image.open(photo).convert('RGB')).astype(np.float32)
    src = np.array(Image.open(source).convert('RGB')).astype(np.float32)[sy0:sy1, sx0:sx1]

    w, h = dx1 - dx0, dy1 - dy0
    ovale = os.environ.get('OVALE') == '1'
    etirer = ovale or os.environ.get('ETIRER') == '1'
    hs = h if etirer else int(round(src.shape[0] * w / src.shape[1]))
    src = cv2.resize(src, (w, hs), interpolation=cv2.INTER_CUBIC)

    # étiquette à la taille de la cible : papier prolongé (couleur des bords haut et bas)
    etiq = np.empty((h, w, 3), np.float32)
    if hs >= h:
        off = (hs - h) // 2
        etiq[:] = src[off:off + h]
    else:
        haut = (h - hs) // 2
        etiq[:haut] = src[3:9].mean(axis=(0, 1), keepdims=True)
        etiq[haut:haut + hs] = src
        etiq[haut + hs:] = src[-9:-3].mean(axis=(0, 1), keepdims=True)

    # transfert d'éclairage : basse fréquence de la cible / basse fréquence de la vraie étiquette
    cible = img[dy0:dy1, dx0:dx1]
    visible = np.ones((h, w), bool)
    for i in range(0, len(caches), 4):
        cx0, cy0, cx1, cy1 = caches[i:i + 4]
        visible[max(cy0 - dy0, 0):max(cy1 - dy0, 0), max(cx0 - dx0, 0):max(cx1 - dx0, 0)] = False
    visible_rect = visible.copy()
    if os.environ.get('CACHE_POLY'):   # parties cachées en polygone (bord courbe d'une bouteille devant)
        m = np.zeros(img.shape[:2], np.uint8)
        for poly in os.environ['CACHE_POLY'].split(';'):
            pts = np.array([list(map(int, p.split(','))) for p in poly.split()], np.int32)
            cv2.fillPoly(m, [pts], 255)
        m = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 0.8)[dy0:dy1, dx0:dx1]
        visible = visible & (m < 0.5)
        douceur = 1 - m
    else:
        douceur = None
    # éclairage mesuré seulement sur la partie visible (les produits devant ne doivent pas l'assombrir)
    remplie = cible.copy()
    remplie[~visible] = np.median(cible[visible], axis=0)
    if os.environ.get('GAIN'):
        # étiquette posée sur du verre (pas sur une ancienne étiquette) : pas de transfert d'éclairage,
        # seulement un gain par canal pour l'accorder à l'exposition de la scène, et un léger ombrage
        # latéral (lumière venant de la gauche)
        g = np.array(list(map(float, os.environ['GAIN'].split(','))), np.float32)
        etiq = etiq * g * np.linspace(1.04, 0.86, w, dtype=np.float32)[None, :, None]
    else:
        lf_c = basse_frequence(remplie, 18)
        lf_e = basse_frequence(etiq, 18)
        etiq = etiq * (lf_c / np.maximum(lf_e, 1))

    # bords fondus sur 3 px (FONDU=n pour plus, ex. étiquette imprimée sur le verre)
    f = int(os.environ.get('FONDU', '3'))
    a = np.ones((h, w), np.float32)
    r = np.linspace(0, 1, f + 1, dtype=np.float32)[1:]
    a[:, :f] *= r
    a[:, -f:] *= r[::-1]
    a[:f, :] *= r[:, None]
    a[-f:, :] *= r[::-1][:, None]
    if ovale:
        a = np.zeros((h, w), np.float32)
        cv2.ellipse(a, (w // 2, h // 2), (w // 2 - 1, h // 2 - 1), 0, 0, 360, 1.0, -1)
        a = cv2.GaussianBlur(a, (0, 0), 1.0)
    a = a * visible_rect
    if douceur is not None:
        a = a * douceur
    a = a[..., None]
    img[dy0:dy1, dx0:dx1] = cible * (1 - a) + etiq * a

    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(sortie, quality=95)
    print(sortie)


if __name__ == '__main__':
    main()
