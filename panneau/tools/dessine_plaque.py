"""Dessine une plaque-étiquette simple (cartouche aux bouts arrondis, filet, petit ornement rond à chaque bout,
texte centré) à la place d'une plaque inventée par l'IA, quand la photo du vrai produit ne permet pas de
la reprendre (plaque penchée, en partie cachée).

Usage (depuis panneau/) :
    python3 tools/dessine_plaque.py entree.jpg sortie.jpg X0 Y0 X1 Y1 "TEXTE" FOND_R,G,B PLAQUE_R,G,B TEXTE_R,G,B FILET_R,G,B
      X0..Y1 : boîte à recouvrir (le fond autour de la plaque y est repeint en FOND)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
S = 8  # suréchantillonnage

entree, sortie = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = map(int, sys.argv[3:7])
texte = sys.argv[7]
fond, plaque, encre, filet = (tuple(map(int, a.split(','))) for a in sys.argv[8:12])
img = Image.open(entree).convert('RGB')
w, h = (x1 - x0) * S, (y1 - y0) * S
im = Image.new('RGB', (w, h), fond)
d = ImageDraw.Draw(im)
m = int(1.2 * S)
r = (h - 2 * m) // 2
d.rounded_rectangle((m, m, w - m, h - m), radius=r, fill=plaque, outline=filet, width=max(1, S // 2))
d.rounded_rectangle((m + S, m + S, w - m - S, h - m - S), radius=r - S, outline=filet, width=max(1, S // 4))
for cx in (m + r, w - m - r):          # petits ornements ronds aux deux bouts
    d.ellipse((cx - r * 0.45, h / 2 - r * 0.45, cx + r * 0.45, h / 2 + r * 0.45), outline=encre, width=max(1, S // 3))
f = ImageFont.truetype(str(RACINE / 'public/fonts/Montserrat.ttf'), 10)
try:
    f.set_variation_by_name('Regular')
except Exception:
    pass
# taille : hauteur des capitales = 45 % de la plaque
hc = f.getbbox('H')[3] - f.getbbox('H')[1]
f = ImageFont.truetype(str(RACINE / 'public/fonts/Montserrat.ttf'), max(4, int(10 * (h * 0.42) / hc)))
try:
    f.set_variation_by_name('Regular')
except Exception:
    pass
bb = d.textbbox((0, 0), texte, font=f)
tw = bb[2] - bb[0]
limite = w - 2 * (m + 2 * r)
if tw > limite:                          # trop long : on resserre en réduisant la taille
    f = ImageFont.truetype(str(RACINE / 'public/fonts/Montserrat.ttf'), int(f.size * limite / tw))
    try:
        f.set_variation_by_name('Regular')
    except Exception:
        pass
    bb = d.textbbox((0, 0), texte, font=f)
    tw = bb[2] - bb[0]
th = f.getbbox('H')[3] - f.getbbox('H')[1]
d.text(((w - tw) / 2 - bb[0], (h - th) / 2 - f.getbbox('H')[1]), texte, font=f, fill=encre)
petit = im.resize((x1 - x0, y1 - y0), Image.LANCZOS)
a = np.array(img).astype(np.float32)
p = np.array(petit).astype(np.float32)
# bords de la boîte fondus sur 1 px dans le fond
al = np.ones(p.shape[:2], np.float32)
al[0, :] = al[-1, :] = al[:, 0] = al[:, -1] = 0.5
a[y0:y1, x0:x1] = a[y0:y1, x0:x1] * (1 - al[..., None]) + p * al[..., None]
Image.fromarray(a.clip(0, 255).astype(np.uint8)).save(sortie, quality=95)
print(sortie)
