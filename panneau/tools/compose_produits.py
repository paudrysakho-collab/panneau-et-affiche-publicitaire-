"""Photo de groupe composée à partir des VRAIS produits détourés, un par un (aucune IA) : chaque produit à sa
hauteur réelle, posé sur une marche, avec ombre de contact, ombre portée (lumière de gauche) et reflet.
Les étiquettes ne sont jamais retouchées : ce sont les photos d'origine.

Sortie : PNG transparent (le fond de l'affiche apparaît derrière), comme vitrine_claire_13.png.

Usage (depuis panneau/) :
    python3 tools/compose_produits.py MODELE TEINTE sortie.png
      MODELE : rangee (marche basse, pots devant) | gradins (marche haute, petits produits devant)
      TEINTE : sombre (marche noire brillante, verre clair rendu transparent) | clair (marche crème)
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

D = Path('bouteilles-gemini/detoures')
P = Path('bouteilles-gemini/pack-derniere-tentative')
PX_CM = 40                                   # résolution : 40 px par cm réel

# hauteur réelle (cm) ; zone d'étiquette dans l'image du pack (fractions x0, y0, x1, y1), protégée du
# traitement « verre » ; verre : le produit a du verre clair (ou cellophane) qui laisse voir le fond blanc
PRODUITS = {
    1: dict(nom='01_rhum_La_Favorite_Coeur_de_Canne', h=27.0, etiq=(0.05, 0.53, 0.95, 0.93), verre=True),
    2: dict(nom='02_jus_de_raisin_Syrah', h=17.5, etiq=(0.15, 0.44, 0.85, 0.86), verre=False),
    3: dict(nom='03_whisky_Suntory_Toki', h=25.0, etiq=(0.06, 0.37, 0.96, 0.62), verre=True),
    4: dict(nom='04_whisky_Tomatin_Legacy', h=26.0, etiq=(0.05, 0.50, 0.95, 0.81), verre=True),
    5: dict(nom='05_rose_Bastide_de_Blacailloux_JOIO', h=31.0, etiq=(0.13, 0.40, 0.87, 0.82), verre=True,
            autres=[(0.0, 0.0, 1.0, 0.21)]),                     # capsule crème
    6: dict(nom='06_rouge_Chateauneuf-du-Pape_Prieure_des_Papes', h=30.0, etiq=(0.04, 0.66, 0.96, 0.96), verre=False),
    7: dict(nom='07_rouge_Chateau_de_Gragnos_Lou_Daro', h=30.0, etiq=(0.04, 0.58, 0.96, 0.92), verre=False),
    8: dict(nom='08_champagne_Denis_Frezier_Cuvee_des_Trois_Crus', h=30.0, etiq=(0.08, 0.67, 0.92, 0.95), verre=False),
    9: dict(nom='09_biere_Lutgarde_Blonde', h=18.5, etiq=(0.08, 0.40, 0.95, 0.92), verre=False),
    10: dict(nom='10_biere_Trompe_Souris_Blonde', h=23.0, etiq=(0.0, 0.50, 1.0, 0.95), verre=False),
    11: dict(nom='11_chocolats_Maison_Guinguet', h=23.0, etiq=(0.0, 0.55, 1.0, 1.0), verre=True,
             autres=[(0.25, 0.08, 0.75, 0.36)]),                 # rose en papier
    12: dict(nom='12_terrine_Gouts_de_Loire_Silure', h=8.0, etiq=(0.0, 0.25, 1.0, 0.92), verre=False),
    13: dict(nom='13_tartinable_courgettes_Atelier_d_Emile', h=8.5, etiq=(0.0, 0.40, 1.0, 1.0), verre=True),
}

# placements : rangée « haut » = sur la marche, « bas » = au sol devant ; ecart = espace avant le produit (cm)
MODELES = {
    'rangee': dict(marche=7.0, haut=[(1, 0), (2, 1.0), (3, 1.0), (4, 1.0), (5, 1.0), (6, 1.0), (7, 1.0), (8, 1.0),
                                      (10, 1.0), (9, 1.0), (11, 1.0)],
                   bas=[(12, 'centre', -5.5), (13, 'centre', 5.0)]),
    'gradins': dict(marche=20.0, haut=[(1, 0), (3, 1.2), (4, 1.2), (5, 1.2), (6, 1.2), (7, 1.2), (8, 1.2),
                                       (10, 1.2), (11, 1.2)],
                    bas=[(2, 'frac', 0.24), (12, 'frac', 0.43), (13, 'frac', 0.585), (9, 'frac', 0.76)], avant=1.2),
}


def charge(num, sombre, echelle=1.0):
    """Produit détouré, mis à l'échelle réelle ; en version sombre, le verre clair laisse voir le fond."""
    p = PRODUITS[num]
    im = np.array(Image.open(D / f"{p['nom']}.png").convert('RGBA')).astype(np.float32)
    rgb, a = im[..., :3], im[..., 3] / 255
    if num == 11:                               # torsade du sachet coupée par le cadre d'origine : fondu
        n = int(a.shape[0] * 0.10)
        a[:n] *= np.linspace(0, 1, n)[:, None] ** 1.5
    if sombre and p['verre']:
        # zone d'étiquette protégée : position du détourage dans l'image du pack (correspondance exacte)
        pack = np.array(Image.open(P / f"{p['nom']}.jpg").convert('RGB')).astype(np.float32)
        ph, pw = pack.shape[:2]
        x0, y0, x1, y1 = p['etiq']
        prot = np.zeros(a.shape, np.float32)
        r = cv2.matchTemplate(pack.astype(np.uint8), im[..., :3].astype(np.uint8)[:min(200, a.shape[0])],
                              cv2.TM_SQDIFF) if a.shape[0] < ph and a.shape[1] <= pw else None
        if r is not None:
            _, _, (ox, oy), _ = cv2.minMaxLoc(r)
        else:
            ox, oy = 0, 0
        ex0, ey0 = int(x0 * pw) - ox, int(y0 * ph) - oy
        ex1, ey1 = int(x1 * pw) - ox, int(y1 * ph) - oy
        prot[max(0, ey0):max(0, ey1), max(0, ex0):max(0, ex1)] = 1
        for zx0, zy0, zx1, zy1 in p.get('autres', []):        # autres zones opaques (capsule, rose en papier)
            prot[max(0, int(zy0 * ph) - oy):max(0, int(zy1 * ph) - oy), max(0, int(zx0 * pw) - ox):max(0, int(zx1 * pw) - ox)] = 1
        prot = cv2.GaussianBlur(prot, (0, 0), 6)
        # verre vide (fond blanc vu à travers : clair et neutre) -> en partie transparent ; liquides et
        # couleurs du verre -> teinte approfondie (sur fond sombre, un liquide éclairé paraît plus dense)
        f = rgb / 255
        mx, mn = f.max(axis=2), f.min(axis=2)
        sat = (mx - mn) / np.maximum(mx, 1e-3)
        vide = np.clip((mn - 0.80) / 0.15, 0, 1) * np.clip((0.14 - sat) / 0.08, 0, 1)
        neuf = 255 * f ** 1.5
        k = (1 - prot)[..., None]
        rgb = rgb * (1 - k) + neuf * k
        a = a * (1 - 0.72 * vide * k[..., 0])
    h = int(round(p['h'] * PX_CM * echelle))
    w = int(round(a.shape[1] * h / a.shape[0]))
    rgb = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
    a = cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA)
    return rgb, a.clip(0, 1)


class Toile:
    """Calques en prémultiplié (couleur × alpha, alpha), composés de l'arrière vers l'avant."""

    def __init__(self, W, H):
        self.W, self.H = W, H
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.a = np.zeros((H, W), np.float32)

    def pose(self, rgb, a, x, y):
        H, W = self.H, self.W
        h, w = a.shape
        xa, ya, xb, yb = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if xa >= xb or ya >= yb:
            return
        aa = a[ya - y:yb - y, xa - x:xb - x]
        cc = rgb[ya - y:yb - y, xa - x:xb - x] if rgb.ndim == 3 else np.broadcast_to(rgb, (yb - ya, xb - xa, 3))
        self.rgb[ya:yb, xa:xb] = cc * aa[..., None] + self.rgb[ya:yb, xa:xb] * (1 - aa[..., None])
        self.a[ya:yb, xa:xb] = aa + self.a[ya:yb, xa:xb] * (1 - aa)

    def image(self):
        out = np.zeros((self.H, self.W, 4), np.float32)
        out[..., :3] = self.rgb / np.maximum(self.a[..., None], 1e-4)
        out[..., 3] = self.a * 255
        return Image.fromarray(out.clip(0, 255).astype(np.uint8), 'RGBA')


def ombres(toile, a, x, y_base, sombre):
    """Ombre de contact sous la base et ombre portée vers la droite (lumière de gauche), sur le sol."""
    h, w = a.shape
    teinte = np.array([10, 4, 6] if sombre else [70, 52, 42], np.float32)
    # ombre de contact : ellipse sous la base
    cont = np.zeros((int(0.12 * w) + 40, w + 40), np.float32)
    cv2.ellipse(cont, (cont.shape[1] // 2, cont.shape[0] // 2), (int(w * 0.48), max(3, int(0.035 * w))),
                0, 0, 360, 1, -1)
    cont = cv2.GaussianBlur(cont, (0, 0), max(2, w * 0.025)) * (0.85 if sombre else 0.55)
    toile.pose(teinte, cont, x - 20, y_base - cont.shape[0] // 2)
    # ombre portée : silhouette aplatie, glissée vers la droite
    hh = max(4, int(h * 0.10))
    sil = cv2.resize(a, (w, hh), interpolation=cv2.INTER_AREA)[::-1]
    dec = np.zeros((hh, w + int(h * 0.35)), np.float32)
    for i in range(hh):                       # cisaillement : plus on s'éloigne de la base, plus ça glisse
        s = int(i / hh * h * 0.35)
        dec[i, s:s + w] = sil[i]
    dec = cv2.GaussianBlur(dec, (0, 0), max(2, h * 0.012)) * (0.45 if sombre else 0.22)
    toile.pose(teinte, dec[::-1], x + int(w * 0.15), y_base - hh + int(hh * 0.15))


def reflet(toile, rgb, a, x, y_base, longueur, force):
    """Reflet inversé sous la base, qui s'estompe."""
    h, w = a.shape
    n = min(h, int(longueur))
    r_rgb, r_a = rgb[::-1][:n], a[::-1][:n] * np.linspace(force, 0, n)[:, None] ** 1.2
    r_rgb = cv2.GaussianBlur(r_rgb, (0, 0), 1.5)
    toile.pose(r_rgb, r_a, x, y_base + 2)


def main():
    modele, teinte, sortie = sys.argv[1:4]
    sombre = teinte == 'sombre'
    M = MODELES[modele]
    haut = [(n, e, *charge(n, sombre)) for n, e in M['haut']]
    bas = [(n, pos, dx, *charge(n, sombre, M.get('avant', 1.35))) for n, pos, dx in M['bas']]
    marge = 3 * PX_CM
    largeur = sum(int(e * PX_CM) + x[3].shape[1] for x in haut for e in [x[1]]) + 2 * marge
    h_max = max(x[3].shape[0] for x in haut)
    S = int(M['marche'] * PX_CM)                # hauteur de la marche
    prof = int(3.0 * PX_CM)                     # épaisseur visible du dessus de la marche (vue un peu plongeante)
    h_bas = max([x[4].shape[0] for x in bas] + [0])
    sol = max(int(4 * PX_CM), h_bas - S + int(5.0 * PX_CM))   # sol devant : les produits du bas restent sous l arête
    H = int(h_max + prof + S + sol + 3 * PX_CM)
    W = largeur
    y_dessus = H - sol - S - prof               # haut du dessus de la marche
    y_base_haut = y_dessus + int(prof * 0.62)   # les produits du haut sont posés au milieu du dessus
    y_face = y_dessus + prof                    # haut de la face avant
    y_sol = H - sol                             # pied de la marche
    y_base_bas = H - int(4.5 * PX_CM)
    t = Toile(W, H)

    # 1. marche : dessus (plus clair) et face avant (dégradé), sur toute la largeur
    x0m, x1m = int(PX_CM * 1.0), W - int(PX_CM * 1.0)
    if sombre:
        dessus, face_h, face_b = np.array([34, 18, 22]), np.array([20, 9, 12]), np.array([8, 3, 5])
    else:
        dessus, face_h, face_b = np.array([252, 248, 242]), np.array([244, 237, 227]), np.array([228, 218, 204])
    m = np.zeros((H, W), np.float32)
    m[y_dessus:y_sol, x0m:x1m] = 1
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    col = np.zeros((H, W, 3), np.float32)
    col[y_dessus:y_face] = dessus
    tt = np.linspace(0, 1, y_sol - y_face)[:, None, None]
    col[y_face:y_sol] = face_h * (1 - tt) + face_b * tt
    col[y_face:y_face + 3] = dessus * 1.25 if sombre else np.array([255, 253, 249])   # arête éclairée
    # ombre douce de la marche sur le sol
    om = np.zeros((H, W), np.float32)
    om[y_sol:y_sol + int(sol * 0.5), x0m:x1m] = np.linspace(0.55 if sombre else 0.20, 0, int(sol * 0.5))[:, None]
    om = cv2.GaussianBlur(om, (0, 0), PX_CM * 0.6)
    t.pose(np.array([0, 0, 0] if sombre else [90, 70, 55], np.float32), om, 0, 0)
    t.pose(col, m, 0, 0)

    # 2. produits du haut, de gauche à droite (ombres puis reflet sur la marche, puis produit)
    x = marge
    places = []
    for n, e, rgb, a in haut:
        x += int(e * PX_CM)
        places.append((n, x, rgb, a))
        x += a.shape[1]
    for n, x, rgb, a in places:
        ombres(t, a, x, y_base_haut, sombre)
    for n, x, rgb, a in places:
        reflet(t, rgb, a, x, y_base_haut, min(a.shape[0] * 0.35, (y_sol - y_base_haut) * 0.95), 0.20 if sombre else 0.12)
    for n, x, rgb, a in places:
        t.pose(rgb, a, x, y_base_haut - a.shape[0])

    # 3. produits du bas, devant la marche
    centre = W // 2
    for n, pos, dx, rgb, a in bas:
        w = a.shape[1]
        if pos == 'frac':                       # centre du produit à une fraction de la largeur
            xb = int(dx * W) - w // 2
        elif pos == 'centre':
            xb = centre + int(dx * PX_CM) - (w if dx < 0 else 0)
        elif pos == 'gauche':
            xb = marge + int(dx * PX_CM)
        else:
            xb = W - marge - int(dx * PX_CM) - w
        ombres(t, a, xb, y_base_bas, sombre)
        reflet(t, rgb, a, xb, y_base_bas, a.shape[0] * 0.35, 0.20 if sombre else 0.10)
        t.pose(rgb, a, xb, y_base_bas - a.shape[0])

    img = t.image()
    img.save(sortie, optimize=True)
    print(sortie, W, 'x', H, 'ratio', round(W / H, 3))


if __name__ == '__main__':
    main()
