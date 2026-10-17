"""Recolore le fond de la photo de groupe (décor, marche et sol) pour une autre couleur d'affiche,
sans toucher aux produits : le stop-trottoir existe en plusieurs fonds, la photo doit suivre.

Le fond est repeint par sa luminance, passée dans une rampe de trois couleurs (ombre, demi-teinte,
lumière) : les dégradés, la marche et le sol gardent leur modelé, seule la teinte change.
Les reflets vifs du sol (l'ambre des bouteilles) gardent leur couleur d'origine, sinon le sol ciré
ne reflèterait plus que le décor.

Usage (depuis panneau/) :
    python3 tools/photo_couleur.py photo-finale.png sortie.jpg vert
      CACHE_ALPHA=chemin.npy garde le détourage BiRefNet entre deux essais (~1 min).
"""
import os
import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# rampe de chaque fond : (ombre, demi-teinte, lumière), en RVB
FONDS = {
    'vin': ((10, 3, 4), (74, 26, 32), (150, 72, 72)),          # lie-de-vin : la photo d'origine
    'grenat': ((18, 4, 7), (122, 26, 42), (205, 96, 92)),      # grenat vif, plus lumineux
    'vert': ((5, 15, 10), (18, 64, 42), (92, 150, 110)),       # vert bouteille
    'bleu': ((4, 10, 18), (18, 50, 82), (96, 142, 190)),       # bleu nuit
    'nuit': ((8, 8, 9), (46, 44, 46), (150, 146, 142)),        # anthracite
}


def rampe(lum, couleurs):
    """Luminance 0-1 -> couleur, en passant par la demi-teinte à 0,5."""
    c0, c1, c2 = (np.array(c, np.float32) for c in couleurs)
    t = np.clip(lum, 0, 1)[..., None]
    bas = c0 + (c1 - c0) * (t / 0.5)
    haut = c1 + (c2 - c1) * ((t - 0.5) / 0.5)
    return np.where(t < 0.5, bas, haut)


def lisse(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def alpha_produits(src, cache, taille):
    """Détourage des produits, ramené à la taille de l'image traitée (le cache peut venir d'une
    version plus petite : le détourage est lent, la photo HD est le même cadrage agrandi)."""
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
    src, sortie, fond = sys.argv[1:4]
    rvb = np.array(Image.open(src).convert('RGB'), np.float32)
    a = alpha_produits(src, os.environ.get('CACHE_ALPHA'), (rvb.shape[1], rvb.shape[0]))

    lum = (rvb * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(axis=2) / 255
    # la photo d'origine est sombre : sa luminance est étirée avant la rampe, sinon tout tombe dans l'ombre
    repeint = rampe(np.clip(lum * 1.45, 0, 1), FONDS[fond])

    # les reflets vifs (ambre des bouteilles dans le sol ciré) gardent leur couleur
    garde = lisse(lum, 0.40, 0.62)[..., None]
    repeint = repeint * (1 - garde) + rvb * garde

    # seuls les pixels hors produits changent
    m = (1 - a)[..., None]
    out = np.clip(rvb * (1 - m) + repeint * m, 0, 255).astype(np.uint8)
    img = Image.fromarray(out)
    if sortie.lower().endswith(('.jpg', '.jpeg')):
        img.save(sortie, quality=95, subsampling=0)
    else:
        img.save(sortie)
    print('fond', fond, '->', sortie)


if __name__ == '__main__':
    main()
