"""Photo de la version claire de l'affiche, à partir de la photo de groupe validée par le client
(fond lie-de-vin, marche noire, sol brillant) : les produits sont détourés et reposés sur un décor clair
transparent, marche crème à la place de la marche noire, ombres de contact et reflets doux sur le sol.
Le PNG garde la transparence : le fond crème de l'affiche claire apparaît derrière.

Usage (depuis panneau/) :
    python3 tools/photo_claire_finale.py bouteilles-gemini/photo-finale.png public/produits/photo_finale_claire.png
      CACHE_ALPHA=chemin.npy garde le détourage BiRefNet entre deux essais (~1 min).
"""
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None

# repères verticaux, en pixels de la photo (1672 x 941), relevés sur le profil de luminance :
PLATEAU = (631, 667)     # dessus de la marche, là où posent les 11 bouteilles
FACADE = (667, 788)      # face avant de la marche (granit noir sur la photo)
SOL = 788                # début du sol brillant, où posent les terrines et les chocolats

# décor clair : dessus de marche, face avant, sol (RVB)
CREME_HAUT = (245, 236, 221)
CREME_BAS = (236, 226, 209)
FACADE_HAUT = (226, 212, 192)
FACADE_BAS = (207, 191, 168)
SOL_CLAIR = (242, 234, 222)


def degrade(largeur, haut, bas, couleur_haut, couleur_bas):
    """Bande horizontale en dégradé vertical de couleur_haut à couleur_bas."""
    n = bas - haut
    t = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    c = np.array(couleur_haut, np.float32)[None, :] * (1 - t) + np.array(couleur_bas, np.float32)[None, :] * t
    return np.repeat(c[:, None, :], largeur, axis=1)


def alpha_produits(src, cache):
    if cache and os.path.exists(cache):
        return np.load(cache).astype(np.float32) / 255
    from rembg import new_session, remove
    a = np.array(remove(Image.open(src).convert('RGB'), session=new_session('birefnet-general')))[..., 3]
    if cache:
        np.save(cache, a)
    return a.astype(np.float32) / 255


def main():
    src, sortie = sys.argv[1:3]
    photo = Image.open(src).convert('RGB')
    W, H = photo.size
    rvb = np.array(photo, np.float32)
    a = alpha_produits(src, os.environ.get('CACHE_ALPHA'))

    # ---- décor clair ----
    decor = np.zeros((H, W, 3), np.float32)
    decor[:PLATEAU[0]] = SOL_CLAIR                                   # fond : laissé transparent ensuite
    decor[PLATEAU[0]:PLATEAU[1]] = degrade(W, *PLATEAU, CREME_HAUT, CREME_BAS)
    decor[FACADE[0]:FACADE[1]] = degrade(W, *FACADE, FACADE_HAUT, FACADE_BAS)
    decor[FACADE[1]:] = degrade(W, FACADE[1], H, SOL_CLAIR, (246, 239, 229))
    # arête claire en haut de la face avant
    decor[FACADE[0]:FACADE[0] + 2] = np.array((250, 245, 236), np.float32)
    # les changements de plan d'une marche de pierre ne sont jamais au couteau : adouci verticalement
    sigma = 5.0
    k = np.exp(-0.5 * (np.arange(-15, 16) / sigma) ** 2).astype(np.float32)
    k /= k.sum()
    pad = np.pad(decor, ((15, 15), (0, 0), (0, 0)), mode='edge')
    decor = np.einsum('i,ijkl->jkl', k, np.stack([pad[i:i + H] for i in range(31)]))

    # opacité du décor : la marche est pleine, le fond derrière reste transparent,
    # le sol s'efface vers le bas pour fondre dans le fond de l'affiche.
    op = np.zeros((H, 1), np.float32)
    op[PLATEAU[0]:FACADE[1]] = 1
    op[:PLATEAU[0]] = 0
    fondu = np.linspace(1, 0, H - FACADE[1], dtype=np.float32) ** 0.7
    op[FACADE[1]:, 0] = fondu
    # raccord doux en haut du plateau (la marche n'a pas de bord net à l'arrière)
    n = 14
    op[PLATEAU[0]:PLATEAU[0] + n, 0] = np.linspace(0, 1, n)
    op = np.repeat(op[:, :, None], W, axis=1)

    # ---- ombres de contact ----
    # bouteilles : empreinte de leur base, étalée vers le bas sur le dessus de la marche
    ombre = np.zeros((H, W), np.float32)
    base_b = a[PLATEAU[0] - 8:PLATEAU[0] + 2].max(axis=0)
    for i in range(34):
        y = PLATEAU[0] - 4 + i
        if 0 <= y < H:
            ombre[y] = np.maximum(ombre[y], base_b * (1 - i / 34) ** 1.1)
    # terrines et chocolats : empreinte de leur base sur le sol
    bas_objets = np.zeros(W, np.float32)
    for x in range(W):
        col = np.nonzero(a[SOL:, x] > 0.5)[0]
        if len(col):
            bas_objets[x] = SOL + col.max()
    for x in range(W):
        yb = int(bas_objets[x])
        if yb:
            for i in range(22):
                y = yb - 4 + i
                if 0 <= y < H:
                    ombre[y, x] = max(ombre[y, x], (1 - i / 22) ** 1.2)
    ombre = np.array(Image.fromarray((ombre * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7)), np.float32) / 255
    decor *= (1 - 0.68 * ombre)[:, :, None]

    # ---- reflets doux sur le sol ----
    # les produits se reflètent dans le sol ciré : copie retournée, floutée, très peu opaque
    reflet_rvb = np.zeros((H, W, 3), np.float32)
    reflet_a = np.zeros((H, W), np.float32)
    for depart, hauteur in ((PLATEAU[0], FACADE[1] - PLATEAU[0]), (SOL, H - SOL)):
        src_h = min(hauteur, depart)
        bloc = rvb[depart - src_h:depart][::-1]
        bloc_a = a[depart - src_h:depart][::-1]
        fin = min(H, depart + src_h)
        reflet_rvb[depart:fin] = bloc[:fin - depart]
        reflet_a[depart:fin] = np.maximum(reflet_a[depart:fin], bloc_a[:fin - depart])
    # le reflet s'éteint vers le bas
    attenue = np.ones(H, np.float32)
    attenue[PLATEAU[0]:] = 1 - np.linspace(0, 0.85, H - PLATEAU[0], dtype=np.float32)
    reflet_a *= 0.13 * attenue[:, None]
    reflet_rvb = np.array(Image.fromarray(reflet_rvb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(9)), np.float32)
    reflet_a = np.array(Image.fromarray((reflet_a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4)), np.float32) / 255
    # le reflet éclaircit peu : mélangé au décor, sans sortir de la marche ni du sol
    reflet_a *= op[:, :, 0]
    decor = decor * (1 - reflet_a[:, :, None]) + reflet_rvb * reflet_a[:, :, None]

    # ---- produits par-dessus ----
    sortie_rvb = decor * op + rvb * 0  # décor seul là où il n'y a pas de produit
    sortie_a = op[:, :, 0].copy()
    sortie_rvb = sortie_rvb * (1 - a[:, :, None]) + rvb * a[:, :, None]
    sortie_a = np.clip(sortie_a * (1 - a) + a, 0, 1)

    img = np.dstack([np.clip(sortie_rvb, 0, 255), np.clip(sortie_a * 255, 0, 255)]).astype(np.uint8)
    Image.fromarray(img, 'RGBA').save(sortie)
    print('version claire', sortie, Image.open(sortie).size)


if __name__ == '__main__':
    main()
