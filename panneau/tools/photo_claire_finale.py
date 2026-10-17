"""Photo de la version claire de l'affiche, à partir de la photo de groupe validée par le client
(fond lie-de-vin, marche noire, sol brillant) : les produits sont détourés et reposés sur un décor clair
transparent, marche crème à la place de la marche noire, ombres de contact et reflets doux sur le sol.
Le PNG garde la transparence : le fond crème de l'affiche claire apparaît derrière.

Usage (depuis panneau/) :
    python3 tools/photo_claire_finale.py bouteilles-gemini/photo-finale.png public/produits/photo_finale_claire.png
      3e argument : teinte du décor selon le fond de l'affiche (creme par défaut, ou safran, corail, anis…).
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

# teinte du décor selon le fond de l'affiche : la pierre prend la couleur de la lumière ambiante,
# sinon la marche fait une bande blanche posée sur un fond coloré. Valeurs = le fond de la palette
# (src/Panneau.tsx), appliquées en produit à FORCE.
TEINTES = {
    'creme': None,
    'safran': '#eeb63f',
    'pourpre': '#c586b3',
    'violet': '#ae63c2',
    'parme': '#d7b6e6',
    'corail': '#f0836a',
    'anis': '#c3d94f',
    'turquoise': '#5fc6cf',
    'framboise': '#ef7f9e',
}
FORCE = 0.33


def multiplicateur(nom):
    """Produit à appliquer au décor crème pour le fondre dans le fond de l'affiche."""
    hexa = TEINTES[nom]
    if hexa is None:
        return np.ones(3, np.float32)
    c = np.array([int(hexa[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255
    return (1 - FORCE) + FORCE * c


def degrade(largeur, haut, bas, couleur_haut, couleur_bas):
    """Bande horizontale en dégradé vertical de couleur_haut à couleur_bas."""
    n = bas - haut
    t = np.linspace(0, 1, n, dtype=np.float32)[:, None]
    c = np.array(couleur_haut, np.float32)[None, :] * (1 - t) + np.array(couleur_bas, np.float32)[None, :] * t
    return np.repeat(c[:, None, :], largeur, axis=1)


def alpha_produits(src, cache, taille):
    """Détourage des produits, ramené à la taille de l'image traitée."""
    if cache and os.path.exists(cache):
        a = np.load(cache)
        if (a.shape[1], a.shape[0]) != taille:
            a = np.array(Image.fromarray(a).resize(taille, Image.LANCZOS))
        return a.astype(np.float32) / 255
    from rembg import new_session, remove
    a = np.array(remove(Image.open(src).convert('RGB'), session=new_session('birefnet-general')))[..., 3]
    if cache:
        np.save(cache, a)
    return a.astype(np.float32) / 255


def main():
    src, sortie = sys.argv[1:3]
    teinte = multiplicateur(sys.argv[3] if len(sys.argv) > 3 else 'creme')
    photo = Image.open(src).convert('RGB')
    W, H = photo.size
    rvb = np.array(photo, np.float32)
    a = alpha_produits(src, os.environ.get('CACHE_ALPHA'), (W, H))
    # les repères sont relevés sur la photo d'origine (1672 px de large) : mis à l'échelle
    k = W / 1672

    # ---- décor clair ----
    plateau = (round(PLATEAU[0] * k), round(PLATEAU[1] * k))
    facade = (round(FACADE[0] * k), round(FACADE[1] * k))
    sol = round(SOL * k)

    decor = np.zeros((H, W, 3), np.float32)
    decor[:plateau[0]] = SOL_CLAIR                                   # fond : laissé transparent ensuite
    decor[plateau[0]:plateau[1]] = degrade(W, *plateau, CREME_HAUT, CREME_BAS)
    decor[facade[0]:facade[1]] = degrade(W, *facade, FACADE_HAUT, FACADE_BAS)
    decor[facade[1]:] = degrade(W, facade[1], H, SOL_CLAIR, (246, 239, 229))
    # arête claire en haut de la face avant
    decor[facade[0]:facade[0] + max(2, round(2 * k))] = np.array((250, 245, 236), np.float32)
    # les changements de plan d'une marche de pierre ne sont jamais au couteau : adouci verticalement
    sigma = 5.0 * k
    rayon = max(15, round(3 * sigma))
    noyau = np.exp(-0.5 * (np.arange(-rayon, rayon + 1) / sigma) ** 2).astype(np.float32)
    noyau /= noyau.sum()
    pad = np.pad(decor, ((rayon, rayon), (0, 0), (0, 0)), mode='edge')
    decor = np.einsum('i,ijkl->jkl', noyau, np.stack([pad[i:i + H] for i in range(2 * rayon + 1)]))

    # opacité du décor : la marche est pleine, le fond derrière reste transparent,
    # le sol s'efface vers le bas pour fondre dans le fond de l'affiche.
    op = np.zeros((H, 1), np.float32)
    op[plateau[0]:facade[1]] = 1
    op[:plateau[0]] = 0
    fondu = np.linspace(1, 0, H - facade[1], dtype=np.float32) ** 0.7
    op[facade[1]:, 0] = fondu
    # raccord doux en haut du plateau (la marche n'a pas de bord net à l'arrière)
    n = round(14 * k)
    op[plateau[0]:plateau[0] + n, 0] = np.linspace(0, 1, n)
    op = np.repeat(op[:, :, None], W, axis=1)

    # ---- ombres de contact ----
    # bouteilles : empreinte de leur base, étalée vers le bas sur le dessus de la marche
    ombre = np.zeros((H, W), np.float32)
    base_b = a[plateau[0] - round(8 * k):plateau[0] + round(2 * k)].max(axis=0)
    n_b = round(34 * k)
    for i in range(n_b):
        y = plateau[0] - round(4 * k) + i
        if 0 <= y < H:
            ombre[y] = np.maximum(ombre[y], base_b * (1 - i / n_b) ** 1.1)
    # terrines et chocolats : empreinte de leur base sur le sol
    bas_objets = np.zeros(W, np.float32)
    for x in range(W):
        col = np.nonzero(a[sol:, x] > 0.5)[0]
        if len(col):
            bas_objets[x] = sol + col.max()
    for x in range(W):
        yb = int(bas_objets[x])
        if yb:
            n_o = round(22 * k)
            for i in range(n_o):
                y = yb - round(4 * k) + i
                if 0 <= y < H:
                    ombre[y, x] = max(ombre[y, x], (1 - i / n_o) ** 1.2)
    ombre = np.array(Image.fromarray((ombre * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(7 * k)), np.float32) / 255
    decor *= (1 - 0.68 * ombre)[:, :, None]

    # ---- reflets doux sur le sol ----
    # les produits se reflètent dans le sol ciré : copie retournée, floutée, très peu opaque
    reflet_rvb = np.zeros((H, W, 3), np.float32)
    reflet_a = np.zeros((H, W), np.float32)
    for depart, hauteur in ((plateau[0], facade[1] - plateau[0]), (sol, H - sol)):
        src_h = min(hauteur, depart)
        bloc = rvb[depart - src_h:depart][::-1]
        bloc_a = a[depart - src_h:depart][::-1]
        fin = min(H, depart + src_h)
        reflet_rvb[depart:fin] = bloc[:fin - depart]
        reflet_a[depart:fin] = np.maximum(reflet_a[depart:fin], bloc_a[:fin - depart])
    # le reflet s'éteint vers le bas
    attenue = np.ones(H, np.float32)
    attenue[plateau[0]:] = 1 - np.linspace(0, 0.85, H - plateau[0], dtype=np.float32)
    reflet_a *= 0.13 * attenue[:, None]
    reflet_rvb = np.array(Image.fromarray(reflet_rvb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(9 * k)), np.float32)
    reflet_a = np.array(Image.fromarray((reflet_a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(4 * k)), np.float32) / 255
    # le reflet éclaircit peu : mélangé au décor, sans sortir de la marche ni du sol
    reflet_a *= op[:, :, 0]
    decor = decor * (1 - reflet_a[:, :, None]) + reflet_rvb * reflet_a[:, :, None]

    decor *= teinte[None, None, :]

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
