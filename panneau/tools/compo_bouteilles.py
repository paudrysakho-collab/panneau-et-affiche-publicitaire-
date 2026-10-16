"""Compose les 8 bouteilles détourées en une photo de groupe (sans IA : étiquettes intactes).

Deux rangs en quinconce, proportions réelles, ombres de contact et ombres portées vers la droite
(lumière venant de la gauche, comme la composition terrines/chocolat).

Sorties (dans bouteilles-compo/) :
    compo_bouteilles.png       fond transparent, ombres comprises (pour l'affiche)
    compo_bouteilles_blanc.jpg aperçu sur fond blanc

Usage (depuis panneau/) : python3 tools/compo_bouteilles.py
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

RACINE = Path(__file__).resolve().parent.parent
PRODUITS = RACINE / 'public/produits'
SORTIE = RACINE / 'bouteilles-compo'

PX_CM = 24.4          # 732 px = bouteille de vin de 30 cm, sans agrandissement
ARRIERE = 0.86        # échelle du rang arrière (perspective)
SOL_AVANT = 1000      # ligne de sol du rang avant (px, avant recadrage)
SOL_ARRIERE = 925     # ligne de sol du rang arrière

# (fichier, hauteur réelle cm, centre x, rang)
BOUTEILLES = [
    ('blacailloux.png', 30, 505, 'arriere'),
    ('gragnos_lou_daro.png', 30, 705, 'arriere'),
    ('frezier.png', 30.5, 1265, 'arriere'),
    ('divin_sauvignon_0-0.png', 32, 1465, 'arriere'),
    ('whisky_toki.png', 24, 300, 'avant'),
    ('chateauneuf.png', 30, 870, 'avant'),
    ('balac.png', 30, 1080, 'avant'),
    ('rhum_la_favorite.png', 27, 1660, 'avant'),
]


def ombres(alpha, x, sol, toile):
    """Ombre de contact sous la bouteille + ombre portée étirée vers la droite."""
    w, h = alpha.size
    # contact : ellipse sombre et serrée
    contact = Image.new('L', toile.size, 0)
    ell = Image.new('L', (int(w * 1.15), 26), 0)
    ImageDraw.Draw(ell).ellipse([0, 0, ell.width - 1, ell.height - 1], fill=150)
    contact.paste(ell, (int(x - ell.width / 2 + w * 0.06), int(sol - 13)))
    contact = contact.filter(ImageFilter.GaussianBlur(7))
    # portée : silhouette aplatie et cisaillée vers la droite
    hp = max(int(h * 0.16), 1)
    plat = alpha.resize((w, hp), Image.LANCZOS)
    cis = int(h * 0.55)
    porte = plat.transform((w + cis, hp), Image.AFFINE, (1, -cis / hp, cis, 0, 1, 0), Image.BICUBIC)
    porte = porte.transpose(Image.FLIP_TOP_BOTTOM).point(lambda v: v * 0.30)
    calque = Image.new('L', toile.size, 0)
    calque.paste(porte, (int(x - w / 2), int(sol - hp * 0.15)))
    calque = calque.filter(ImageFilter.GaussianBlur(14))
    return contact, calque


def main():
    toile = Image.new('RGBA', (2600, 1100), (0, 0, 0, 0))
    ombre_totale = Image.new('L', toile.size, 0)
    rangs = {'arriere': [], 'avant': []}
    for fichier, cm, cx, rang in BOUTEILLES:
        im = Image.open(PRODUITS / fichier).convert('RGBA')
        echelle = ARRIERE if rang == 'arriere' else 1.0
        h = round(cm * PX_CM * echelle)
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        rangs[rang].append((im, cx, SOL_ARRIERE if rang == 'arriere' else SOL_AVANT))

    for rang in ('arriere', 'avant'):
        # ombres du rang, puis bouteilles du rang : le rang avant recouvre les ombres arrière
        calque_ombre = np.zeros((toile.height, toile.width), np.uint8)
        for im, cx, sol in rangs[rang]:
            for o in ombres(im.split()[3], cx, sol, toile):
                calque_ombre = np.maximum(calque_ombre, np.array(o))
        noir = Image.new('RGBA', toile.size, (20, 14, 12, 0))
        noir.putalpha(Image.fromarray(calque_ombre))
        toile = Image.alpha_composite(toile, noir)
        for im, cx, sol in rangs[rang]:
            toile.alpha_composite(im, (round(cx - im.width / 2), sol - im.height))

    toile = toile.crop(toile.getbbox())
    SORTIE.mkdir(exist_ok=True)
    toile.save(SORTIE / 'compo_bouteilles.png')
    blanc = Image.new('RGB', (toile.width + 160, toile.height + 120), 'white')
    blanc.paste(toile, (80, 60), toile)
    blanc.save(SORTIE / 'compo_bouteilles_blanc.jpg', quality=93)
    print(toile.size)


if __name__ == '__main__':
    main()
