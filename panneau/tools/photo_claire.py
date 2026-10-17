"""Photo de la version claire de l'affiche, à partir de la photo finale corrigée (fond lie-de-vin) :
les produits (avec leurs vraies étiquettes) sont détourés et posés sur un décor clair transparent :
marche crème à l'arrière (à la place des socles noirs), ombres de contact et léger reflet sur le sol.
Le PNG garde la transparence : le fond de l'affiche claire apparaît derrière.

Usage (depuis panneau/) :
    python3 tools/photo_claire.py photo_corrigee.jpg photo_hd.jpg sortie.png
      photo_corrigee : 1693 x 929 (sert au détourage) ; photo_hd : même photo agrandie (4000 px)
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# socles noirs de la photo (en pixels de la photo 1693 x 929) : remplacés par la marche crème.
# SOCLES_PLEINS : polygones effacés en entier, qui suivent le bord des bouteilles voisines (Syrah,
# Tomatin et son pied évasé, Châteauneuf) ; SOCLES : marges où l'on n'efface que le gris neutre et sombre
# du socle (le verre ambré des bouteilles, plus chaud, reste).
SOCLES_PLEINS = [
    [(348, 670), (404, 670), (404, 700), (402, 706), (400, 712), (398, 718), (348, 718)],
    [(576, 668), (670, 668), (670, 718), (583, 718), (581, 712), (579, 706), (577, 702), (576, 700)],
]
SOCLES = [(344, 664, 408, 720), (568, 664, 674, 720)]
MARCHE = (668, 716)          # haut et bas de la marche (même échelle)


def main():
    src, hd_p, sortie = sys.argv[1:4]
    petit = Image.open(src).convert('RGB')
    cache = os.environ.get('CACHE_ALPHA')      # détourage BiRefNet gardé entre deux essais (~1 min)
    if cache and os.path.exists(cache):
        a = np.load(cache)
    else:
        from rembg import new_session, remove
        a = np.array(remove(petit, session=new_session('birefnet-general')))[..., 3].astype(np.float32) / 255
        if cache:
            np.save(cache, a)
    # socles : hors détourage
    c = np.array(petit).astype(np.float32)
    L = c @ np.array([0.299, 0.587, 0.114], np.float32)
    neutre = (c[..., 0] - c[..., 2]) < 38
    for x0, y0, x1, y1 in SOCLES:
        z = a[y0:y1, x0:x1]
        z[(L[y0:y1, x0:x1] < 45) & neutre[y0:y1, x0:x1]] = 0
    for poly in SOCLES_PLEINS:
        z = np.zeros(a.shape, np.uint8)
        cv2.fillPoly(z, [np.array(poly, np.int32)], 1)
        a[z > 0] = 0
    # liseré sombre du fond d'origine : alpha resserré d'un pixel
    a = cv2.erode(a, np.ones((3, 3), np.uint8))
    a = cv2.GaussianBlur(a, (0, 0), 0.6)

    hd = np.array(Image.open(hd_p).convert('RGB')).astype(np.float32)
    H, W = hd.shape[:2]
    k = W / petit.width
    A = cv2.resize(a, (W, H), interpolation=cv2.INTER_CUBIC).clip(0, 1)

    # calques en prémultiplié : couleur * alpha, alpha
    rgb = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)

    def dessus(c, a2):
        nonlocal rgb, al
        rgb = c * a2[..., None] + rgb * (1 - a2[..., None])
        al = a2 + al * (1 - a2)

    # 1. marche crème (dessus clair, face un peu plus soutenue, ombre douce sur le sol devant)
    y0, y1 = int(MARCHE[0] * k), int(MARCHE[1] * k)
    x0, x1 = int(30 * k), int(1665 * k)
    m = np.zeros((H, W), np.float32)
    m[y0:y1, x0:x1] = 1
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    marche = np.zeros((H, W, 3), np.float32)
    t = np.clip((np.arange(H) - y0) / max(1, y1 - y0), 0, 1)[:, None, None]
    marche[:] = np.array([246, 240, 231], np.float32) * (1 - 0.06 * t)
    dessus_haut = int(y0 + 0.12 * (y1 - y0))
    marche[y0:dessus_haut] = np.array([252, 248, 242], np.float32)
    ombre_sol = np.zeros((H, W), np.float32)
    ombre_sol[y1:y1 + int(10 * k), x0:x1] = np.linspace(0.18, 0, int(10 * k))[:, None]
    ombre_sol = cv2.GaussianBlur(ombre_sol, (0, 0), 3 * k)
    dessus(np.zeros((H, W, 3), np.float32) + np.array([70, 50, 40], np.float32), ombre_sol)
    dessus(marche, m * 0.92)

    # 2. bas de chaque colonne de produit : ombre de contact et reflet sur le sol
    prod = A > 0.5
    bas = np.full(W, -1)
    lignes = np.arange(H)
    for x in range(W):
        ys = lignes[prod[:, x]]
        if len(ys):
            bas[x] = ys.max()
    bas_l = cv2.medianBlur(bas.astype(np.float32).reshape(1, -1), 5).ravel()
    ombre = np.zeros((H, W), np.float32)
    reflet = np.zeros((H, W, 3), np.float32)
    reflet_a = np.zeros((H, W), np.float32)
    n_ref = int(70 * k)
    for x in range(W):
        b = int(bas_l[x])
        if b < 0:
            continue
        ombre[max(0, b - int(2 * k)):min(H, b + int(5 * k)), x] = 0.5
        if b < y1 + 2 * k:      # posé sur la marche : pas de reflet sur le sol
            continue
        n = min(n_ref, H - b - 1, b)
        if n <= 0:
            continue
        reflet[b + 1:b + 1 + n, x] = hd[b - n:b, x][::-1]
        reflet_a[b + 1:b + 1 + n, x] = A[b - n:b, x][::-1] * np.linspace(0.16, 0, n)
    ombre = cv2.GaussianBlur(ombre, (0, 0), 2.5 * k)
    reflet = cv2.GaussianBlur(reflet, (0, 0), 0.8 * k)
    reflet_a = cv2.GaussianBlur(reflet_a, (0, 0), 0.8 * k)
    dessus(np.zeros((H, W, 3), np.float32) + np.array([60, 42, 34], np.float32), ombre * 0.55)
    dessus(reflet, reflet_a)

    # 3. produits
    dessus(hd, A)

    out = np.zeros((H, W, 4), np.float32)
    out[..., :3] = rgb / np.maximum(al[..., None], 1e-4)
    out[..., 3] = al * 255
    Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA').save(sortie, optimize=True)
    print(sortie, W, 'x', H)


if __name__ == '__main__':
    main()
