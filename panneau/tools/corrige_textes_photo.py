"""Corrige les textes inventés par l'IA sur les étiquettes de la photo studio (version sombre).

Pour chaque ligne fautive : on repère les pixels du texte dans la zone (plus sombres ou plus clairs
que le papier, ligne par ligne), on les efface par inpainting, puis on réécrit le vrai texte
(même hauteur de capitales, couleur reprise du texte d'origine), éventuellement limité à une zone
visible quand une autre bouteille passe devant.

Usage (depuis panneau/) :
    python3 tools/corrige_textes_photo.py bouteilles-gemini/resultat_gemini_v8_sombre.jpg public/produits/vitrine_sombre.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
POLICES = {
    'sans': RACINE / 'public/fonts/Montserrat.ttf',
    'serif': RACINE / 'public/fonts/CormorantGaramond.ttf',
    'serif-it': RACINE / 'public/fonts/CormorantGaramond-Italic.ttf',
}
SUR = 8  # suréchantillonnage du rendu du texte

# zone = (x0, y0, x1, y1) contenant l'ancien texte ; mode = 'sombre' (texte plus foncé que le fond) ou 'clair'
# x, y = point d'ancrage (centre des capitales) ; align = 'c' (centré sur x) ou 'g' (commence à x) ou 'd' (finit à x)
# cap = hauteur des capitales en px ; visible = zone où l'on a le droit de dessiner (bouteille devant)
CORRECTIONS = [
    # Jus de raisin Syrah
    dict(zone=(116, 870, 224, 886), mode='sombre', texte='PUR JUS DE RAISINS', police='sans', poids='SemiBold', x=169, y=878, cap=8.0, align='c'),
    dict(zone=(130, 888, 208, 899), mode='sombre', texte='SANS SUCRE AJOUTÉ*', police='sans', poids='Medium', x=169, y=893.5, cap=4.6, align='c'),
    # Whisky Toki (le jus passe devant à gauche)
    dict(zone=(248, 703, 330, 757), mode='sombre', texte=None, cap=5),
    dict(texte='FROM THE HOUSE OF', police='sans', poids='SemiBold', x=236, y=710, cap=4.3, align='g', couleur=(45, 38, 36), visible=(248, 700, 400, 760)),
    dict(texte='SUNTORY WHISKY', police='sans', poids='SemiBold', x=236, y=719.5, cap=4.3, align='g', couleur=(45, 38, 36), visible=(248, 700, 400, 760)),
    dict(texte='ESTABLISHED 1923', police='sans', poids='SemiBold', x=236, y=729, cap=4.3, align='g', couleur=(45, 38, 36), visible=(248, 700, 400, 760)),
    dict(texte='JAPANESE WHISKY', police='serif', poids='Medium', x=236, y=740, cap=4.6, align='g', couleur=(88, 78, 72), visible=(248, 700, 400, 760)),
    dict(texte='43% ALC./VOL. · 70 cl', police='serif', poids='Medium', x=236, y=750, cap=4.3, align='g', couleur=(88, 78, 72), visible=(248, 700, 400, 760)),
    # Bastide de Blacailloux
    dict(zone=(468, 780, 556, 794), mode='sombre', texte='VIN DE PROVENCE', police='sans', poids='SemiBold', x=511, y=787, cap=6.6, align='c'),
    dict(zone=(440, 800, 580, 834), mode='sombre', texte=None, cap=5),
    dict(texte='Famille Chamson Vignerons depuis 1917', police='serif-it', poids='SemiBold', x=510, y=807, cap=4.4, align='c', couleur=(70, 50, 48)),
    dict(texte='COTEAUX VAROIS EN PROVENCE', police='sans', poids='Medium', x=510, y=816.5, cap=4.6, align='c', couleur=(70, 50, 48)),
    dict(texte="APPELLATION D'ORIGINE PROTÉGÉE", police='sans', poids='Regular', x=510, y=825.3, cap=3.2, align='c', couleur=(90, 70, 66)),
    # Château de Gragnos
    dict(zone=(638, 738, 702, 750), mode='sombre', texte='DEPUIS 1710', police='sans', poids='Medium', x=670, y=744.5, cap=4.6, align='c'),
    # Châteauneuf-du-Pape (le pot de terrine passe devant à droite)
    dict(zone=(745, 925, 838, 936), mode='sombre', texte="APPELLATION D'ORIGINE PROTÉGÉE", police='serif', poids='SemiBold', x=748, y=930.5, cap=5.0, align='g', visible=(740, 920, 838, 940)),
    # Château Balac
    dict(zone=(1090, 795, 1166, 811), mode='sombre', texte='SUPÉRIEUR', police='serif', poids='Medium', x=1092, y=803.5, cap=8.6, align='g'),
    dict(zone=(1014, 818, 1130, 832), mode='sombre', texte='FAMILLE TOUCHAIS', police='serif', poids='SemiBold', x=1072, y=825.5, cap=6.4, align='c'),
    # Champagne Denis Frézier (le pot de terrine passe devant à gauche)
    dict(zone=(1222, 813, 1392, 823), mode='sombre', texte='PRODUCED IN THE HEART OF CHAMPAGNE', police='sans', poids='Medium', x=1306, y=818.2, cap=4.6, align='c'),
    dict(zone=(1276, 848, 1394, 882), mode='sombre', texte='Cuvée des Trois Crus', police='serif-it', poids='Medium', x=1388, y=862, cap=10.0, align='d', visible=(1276, 845, 1400, 880)),
    dict(zone=(1268, 912, 1352, 924), mode='sombre', texte='ESTATE BOTTLED', police='sans', poids='Medium', x=1310, y=918, cap=5.6, align='c', visible=(1275, 905, 1400, 930)),
    # Divin (La Favorite passe devant à droite)
    dict(zone=(1434, 843, 1534, 855), mode='sombre', texte='Sans alcool - Alcohol free', police='sans', poids='Medium', italique=True, x=1437, y=849, cap=4.4, align='g', visible=(1430, 840, 1534, 858)),
    # Rhum La Favorite (le sachet passe devant à droite)
    dict(zone=(1606, 769, 1668, 778), mode='sombre', texte='FONDÉE EN 1842', police='sans', poids='SemiBold', x=1637, y=773.5, cap=3.4, align='c'),
    dict(zone=(1592, 845, 1712, 859), mode='sombre', texte='RHUM AGRICOLE AMBRÉ', police='sans', poids='SemiBold', x=1652, y=852, cap=6.4, align='c', visible=(1585, 840, 1712, 862)),
    dict(zone=(1580, 900, 1722, 935), mode='clair', texte=None),
    dict(texte="APPELLATION D'ORIGINE CONTRÔLÉE", police='sans', poids='Medium', x=1648, y=906.5, cap=3.6, align='c', couleur=(214, 200, 175), visible=(1580, 900, 1712, 935)),
    dict(texte='RÉCOLTÉ, DISTILLÉ ET MIS EN BOUTEILLE', police='sans', poids='Medium', x=1648, y=917.5, cap=3.2, align='c', couleur=(214, 200, 175), visible=(1580, 900, 1712, 935)),
    dict(texte='À LA DISTILLERIE LA FAVORITE PAR LA FAMILLE DORMOY', police='sans', poids='Medium', x=1648, y=925, cap=3.2, align='c', couleur=(214, 200, 175), visible=(1580, 900, 1712, 935)),
    # Terrines Goûts de Loire
    dict(zone=(934, 1036, 966, 1052), mode='sombre', texte='BIO', police='sans', poids='Bold', x=949, y=1044, cap=7.2, align='c', couleur=(40, 12, 16)),
    dict(zone=(1158, 1019, 1192, 1033), mode='sombre', texte='BIO', police='sans', poids='Bold', x=1175, y=1026, cap=7.2, align='c'),
    dict(zone=(1070, 999, 1272, 1017), mode='sombre', ecart=7, texte='Touraine Sauvignon et aromates', police='serif-it', poids='Bold', x=1176, y=1005, cap=7.6, align='c', couleur=(12, 16, 30), gras=2.6, visible=(1068, 997, 1270, 1018)),
]

# « à la Tomate séchée » : écriture manuscrite reprise de la photo de référence (où elle est juste).
TOMATE = dict(source=(645, 884, 950, 928), cible=(868, 1005, 1034, 1038), zone=(866, 1006, 1036, 1038))


def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def effacer(img, zone, mode, cap=8, ecart=None):
    """Efface le texte d'une zone : les pixels de texte sont repérés par rapport au fond estimé par
    fermeture (texte sombre) ou ouverture (texte clair) morphologique, puis remplis par inpainting.
    Renvoie les pixels du texte effacé."""
    ecart = ecart or 14
    x0, y0, x1, y1 = zone
    m = 6
    X0, Y0, X1, Y1 = max(0, x0 - m), max(0, y0 - m), x1 + m, y1 + m
    reg = img[Y0:Y1, X0:X1].astype(np.uint8)
    k = int(2 * cap + 5) | 1
    noyau = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    op = cv2.MORPH_CLOSE if mode == 'sombre' else cv2.MORPH_OPEN
    fond = cv2.morphologyEx(reg, op, noyau)
    fond = cv2.GaussianBlur(fond, (0, 0), 1.5)
    L, Lf = lum(reg.astype(float)), lum(fond.astype(float))
    txt = (L < Lf - ecart) if mode == 'sombre' else (L > Lf + ecart)
    dedans = np.zeros_like(txt)
    dedans[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    txt &= dedans
    pix = reg[txt].astype(float)
    # remplissage par inpainting (voisins réels) : pas de halo plus clair autour des lettres
    masque = cv2.dilate(txt.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=2)
    masque[~dedans] = 0
    img[Y0:Y1, X0:X1] = cv2.inpaint(reg, masque, 3, cv2.INPAINT_TELEA)
    return pix


def police(nom, poids, taille):
    f = ImageFont.truetype(str(POLICES[nom]), taille)
    try:
        f.set_variation_by_name(poids)
    except Exception:
        pass
    return f


def rendu(texte, nom, poids, cap, italique=False):
    """Masque alpha du texte, à l'échelle 1, et position du haut des capitales dans ce masque."""
    taille = 200
    f = police(nom, poids, taille)
    h_cap = f.getbbox('H')[3] - f.getbbox('H')[1]
    taille = max(4, round(taille * cap * SUR / h_cap))
    f = police(nom, poids, taille)
    bb = f.getbbox(texte)
    w, h = bb[2] - bb[0] + 8 * SUR, bb[3] - bb[1] + 8 * SUR
    im = Image.new('L', (w, h), 0)
    ImageDraw.Draw(im).text((4 * SUR - bb[0], 4 * SUR - bb[1]), texte, font=f, fill=255)
    if italique:
        im = im.transform((w + h // 4, h), Image.AFFINE, (1, 0.22, -h * 0.22, 0, 1, 0), Image.BICUBIC)
    haut_cap = 4 * SUR - bb[1] + f.getbbox('H')[1]
    petit = im.resize((max(1, round(im.width / SUR)), max(1, round(im.height / SUR))), Image.LANCZOS)
    return np.array(petit).astype(float) / 255, haut_cap / SUR


def poser(img, alpha, gauche, haut, couleur, visible=None):
    H, W = img.shape[:2]
    h, w = alpha.shape
    x0, y0 = int(round(gauche)), int(round(haut))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    a = alpha[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
    if visible:
        vx0, vy0, vx1, vy1 = visible
        clip = np.zeros_like(a)
        cx0, cy0 = max(vx0 - xa, 0), max(vy0 - ya, 0)
        cx1, cy1 = min(vx1 - xa, xb - xa), min(vy1 - ya, yb - ya)
        if cx1 > cx0 and cy1 > cy0:
            clip[cy0:cy1, cx0:cx1] = 1
        a = a * clip
    zone = img[ya:yb, xa:xb].astype(float)
    img[ya:yb, xa:xb] = (zone * (1 - a) + np.array(couleur, float) * a).clip(0, 255).astype(np.uint8)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    img = np.array(Image.open(src).convert('RGB'))
    ref = np.array(Image.open(RACINE / 'bouteilles-gemini/style-reference-terrines-chocolat.jpg').convert('RGB'))

    # 1. effacement des anciens textes (couleur du texte relevée au passage)
    couleurs = []
    for c in CORRECTIONS:
        if 'zone' not in c:
            couleurs.append(None)
            continue
        pix = effacer(img, c['zone'], c['mode'], c.get('cap', 6), c.get('ecart'))
        if len(pix):
            L = lum(pix)
            sel = pix[L <= np.percentile(L, 30)] if c['mode'] == 'sombre' else pix[L >= np.percentile(L, 70)]
            couleurs.append(tuple(sel.mean(axis=0)))
        else:
            couleurs.append((40, 30, 30))
    pix_t = effacer(img, TOMATE['zone'], 'sombre', 6, ecart=18)
    coul_tomate = tuple(pix_t[lum(pix_t) <= np.percentile(lum(pix_t), 30)].mean(axis=0))

    # 2. réécriture du vrai texte
    for c, coul in zip(CORRECTIONS, couleurs):
        if not c.get('texte'):
            continue
        alpha, haut_cap = rendu(c['texte'], c['police'], c['poids'], c['cap'], c.get('italique', False))
        w = alpha.shape[1]
        gauche = {'c': c['x'] - w / 2, 'g': c['x'], 'd': c['x'] - w}[c['align']]
        haut = c['y'] - c['cap'] / 2 - haut_cap
        poser(img, (alpha * c.get('gras', 1)).clip(0, 1), gauche, haut, c.get('couleur', coul), c.get('visible'))

    # 3. « à la Tomate séchée » recopié de la référence
    sx0, sy0, sx1, sy1 = TOMATE['source']
    rouge = ref[sy0:sy1, sx0:sx1, 0].astype(float)
    # sur la bande rouge, l'écriture se lit dans le canal rouge (bande ~200, encre ~40)
    fond = np.percentile(rouge, 90, axis=1, keepdims=True)
    a = ((fond - rouge - 25) / np.maximum(fond - 70, 1)).clip(0, 1)
    tx0, ty0, tx1, ty1 = TOMATE['cible']
    a = cv2.resize(a, (tx1 - tx0, ty1 - ty0), interpolation=cv2.INTER_AREA)
    poser(img, a, tx0, ty0, (40, 12, 16))

    Image.fromarray(img).save(dst, quality=95)
    print(dst)


if __name__ == '__main__':
    main()
