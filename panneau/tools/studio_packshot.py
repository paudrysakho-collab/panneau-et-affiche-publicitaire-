"""Visuel studio Cave 71 : chaque produit retouché SEUL (lumière et matière), puis scène recomposée par code.

Règle : aucune étiquette n'est jamais régénérée. Pour chaque produit :
  1. détourage (alpha des PNG d'entrée, sinon rembg/BiRefNet), bords nettoyés, produit redressé ;
  2. balance des blancs / exposition corrigées par code (gains du fichier de config) ;
  3. retouche IA du produit seul (tools/packshot_ia.py), contrôlée par tools/packshot_controle.py :
     silhouette + lettres (corrélation par tuile) + OCR. Une lettre changée : rejet, nouvel essai (3 au plus) ;
  4. si les 3 essais sont rejetés : on repart du produit d'origine, éclairé par code. Quand un essai IA a la
     même silhouette, son éclairage sert de modèle : sur les étiquettes, seule sa lumière (très lissée) est
     reportée sur les pixels d'origine, jamais ses lettres ; ailleurs (verre, capsules), son rendu est gardé.
     Le résultat repasse le même contrôle des lettres.
Puis la scène est composée sur le fond fixe (studio/background.png, créé une seule fois) : ordre, hauteurs
réelles, reflets (symétrie + flou + dégradé), ombres de contact, spot sur le produit vedette.

Usage (depuis panneau/) :
    python3 tools/studio_packshot.py --entree bouteilles-gemini/detoures --sortie studio/sortie
        [--config studio/config.json] [--fond studio/background.png] [--ia] [--plafond 4.8]
        [--journal bouteilles-gemini/api-essais/depenses.csv] [--seulement 06,04]
Les essais IA déjà faits (sortie/ia/NN_essaiK.png) sont réutilisés sans nouvel appel.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import packshot_controle as K  # noqa: E402

ESSAIS = [('gemini-3-pro-image', '2K'), ('gemini-nano-banana-2.1', '1K'), ('gemini-nano-banana-2.1', '1K')]
FORMATS = {'9:16': 9 / 16, '2:3': 2 / 3, '3:4': 3 / 4, '4:5': 4 / 5, '1:1': 1.0}
H_IA = 1536                       # hauteur du canevas envoyé à l'IA (et de référence du contrôle)


# ---------------------------------------------------------------- fond fixe
def cree_fond(cfg, chemin):
    W, H = cfg['canevas']
    yh, yb = cfg['ligne_horizon'], cfg['ligne_bouteilles']
    y = np.arange(H, dtype=np.float32)[:, None]
    x = np.arange(W, dtype=np.float32)[None, :]
    noir = np.array([11, 4, 7], np.float32)
    lie = np.array([50, 15, 26], np.float32)
    coeur = np.array([100, 37, 42], np.float32)
    cx, cy = W / 2, yb - 560

    def mur_en(yy):
        large = np.exp(-(((x - cx) / (W * 0.60)) ** 2 + ((yy - cy) / 1300) ** 2))
        centre = np.exp(-(((x - cx) / (W * 0.27)) ** 2 + ((yy - cy) / 560) ** 2))
        c = noir + (lie - noir) * large[..., None]
        return c + (coeur - lie) * (centre * large)[..., None]

    mur = mur_en(y)
    # sol noir brillant : reflet atténué et flouté du mur, qui s'éteint en descendant
    d = np.clip(y - yh, 0, None)
    reflet = mur_en(yh - d * 1.8)
    att = (0.24 * np.exp(-d / 420))[..., None]
    sol = noir * 0.8 + reflet * att
    # flaque de lumière sous le produit vedette (au centre)
    flaque = np.exp(-(((x - cx) / 820) ** 2 + ((y - (yb + 70)) / 150) ** 2))[..., None]
    sol = sol + (coeur * 0.30) * flaque * (y > yh)[..., None]
    # liseré brillant au bord du plan (ligne d'horizon), très doux
    lisere = np.exp(-((y - yh - 3) / 4) ** 2)[..., None] * np.exp(-((x - cx) / (W * 0.5)) ** 2)[..., None]
    sol = sol + lisere * np.array([40, 16, 16], np.float32)
    t = np.clip((y - yh + 6) / 12, 0, 1)[..., None]          # transition mur / sol
    img = mur * (1 - t) + sol * t
    img = cv2.GaussianBlur(img, (0, 0), 1.2)
    img += np.random.default_rng(71).uniform(-0.6, 0.6, img.shape).astype(np.float32)   # anti-bandes
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(chemin)
    print('fond créé :', chemin)


# ---------------------------------------------------------------- préparation d'un produit
def charge(entree, fichier):
    p = Path(entree) / fichier
    im = Image.open(p)
    if im.mode != 'RGBA' or np.array(im)[:, :, 3].min() == 255:
        from rembg import new_session, remove
        im = remove(im.convert('RGB'), session=new_session('birefnet-general'))
    a = np.array(im.convert('RGBA')).astype(np.float32) / 255
    ys, xs = np.nonzero(a[:, :, 3] > 0.05)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def nettoie_bords(a):
    """Bords sans halo : la couleur des pixels de bord vient de l'intérieur ; alpha resserré d'un rien."""
    rgb, al = a[:, :, :3], a[:, :, 3]
    plein = (al > 0.97).astype(np.float32)
    plein = cv2.erode(plein, np.ones((3, 3), np.uint8))
    num = cv2.GaussianBlur(rgb * plein[..., None], (0, 0), 2.5)
    den = cv2.GaussianBlur(plein, (0, 0), 2.5)[..., None] + 1e-4
    interieur = num / den
    bord = ((al > 0.01) & (al < 0.97))[..., None]
    rgb = np.where(bord & (den > 0.02), interieur, rgb)
    al = np.clip((al - 0.06) / 0.9, 0, 1)
    return np.dstack([rgb, al])


def inclinaison(a, zone=(0.45, 0.93)):
    al = a[:, :, 3]
    H = al.shape[0]
    xs, ys = [], []
    for yy in range(int(H * zone[0]), int(H * zone[1]), 3):
        r = np.nonzero(al[yy] > 0.5)[0]
        if len(r) > 10:
            xs.append((r[0] + r[-1]) / 2)
            ys.append(yy)
    return math.degrees(math.atan(np.polyfit(ys, xs, 1)[0]))


def redresse(a, angle):
    if abs(angle) < 0.3:
        return a
    h, w = a.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), -angle, 1.0)
    c, s = abs(m[0, 0]), abs(m[0, 1])
    nw, nh = int(h * s + w * c) + 2, int(h * c + w * s) + 2
    m[0, 2] += nw / 2 - w / 2
    m[1, 2] += nh / 2 - h / 2
    pre = a.copy()
    pre[:, :, :3] *= pre[:, :, 3:]
    r = cv2.warpAffine(pre, m, (nw, nh), flags=cv2.INTER_CUBIC, borderValue=(0, 0, 0, 0))
    r = np.clip(r, 0, 1)
    r[:, :, :3] /= np.maximum(r[:, :, 3:], 1e-4)
    ys, xs = np.nonzero(r[:, :, 3] > 0.05)
    return np.clip(r[ys.min():ys.max() + 1, xs.min():xs.max() + 1], 0, 1)


def etalonne(a, gains, gamma=1.0):
    rgb = np.clip(a[:, :, :3] * np.array(gains, np.float32), 0, 1) ** gamma
    return np.dstack([rgb, a[:, :, 3]])


def fond_ia(W, H):
    y = np.linspace(0, 1, H)[:, None, None]
    x = np.linspace(-1, 1, W)[None, :, None]
    g = np.exp(-(x ** 2) / 0.6 - ((y - 0.45) ** 2) / 0.25)
    c0, c1 = np.array([58, 18, 28]), np.array([22, 7, 11])
    return (c1 + (c0 - c1) * g).astype(np.float32) / 255


def canevas_ia(a):
    """Produit centré sur un canevas bordeaux au format d'image le plus serré ; renvoie tout ce qu'il faut."""
    h, w = a.shape[:2]
    r = w / h
    fmt = min((k for k, v in FORMATS.items() if v * 0.86 >= r), key=lambda k: FORMATS[k], default='1:1')
    H = H_IA
    W = int(round(H * FORMATS[fmt] / 8)) * 8
    s = min(0.91 * H / h, 0.86 * W / w)
    ph, pw = int(round(h * s)), int(round(w * s))
    p = cv2.resize(a, (pw, ph), interpolation=cv2.INTER_AREA)
    x0, y0 = (W - pw) // 2, (H - ph) // 2
    fond = fond_ia(W, H)
    M = np.zeros((H, W), np.float32)
    M[y0:y0 + ph, x0:x0 + pw] = p[:, :, 3]
    rgb = fond.copy()
    rgb[y0:y0 + ph, x0:x0 + pw] = p[:, :, :3] * p[:, :, 3:] + fond[y0:y0 + ph, x0:x0 + pw] * (1 - p[:, :, 3:])
    return {'fmt': fmt, 'rgb': (rgb * 255).round().astype(np.uint8), 'M': M, 'fond': fond,
            'boite': (x0, y0, pw, ph), 'produit': p}


def boites_px(zones, boite):
    x0, y0, pw, ph = boite
    return [(int(x0 + z[0] * pw), int(y0 + z[1] * ph), int(x0 + z[2] * pw), int(y0 + z[3] * ph)) for z in zones]


def masque_zones(shape, boites, flou=4):
    Z = np.zeros(shape, np.float32)
    for b in boites:
        Z[b[1]:b[3], b[0]:b[2]] = 1
    return np.clip(cv2.GaussianBlur(Z, (0, 0), flou) * 1.5, 0, 1) if flou else Z


def masque_ia(al, fond):
    """Silhouette du produit dans l'image IA : écart au fond envoyé, trous bouchés."""
    d = np.abs(al.astype(np.float32) / 255 - fond).sum(2)
    m = (d > 0.10).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    cont, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    plein = np.zeros_like(m)
    if cont:
        cv2.drawContours(plein, [max(cont, key=cv2.contourArea)], -1, 1, -1)
    return plein.astype(np.float32)


def basse_freq(img):
    m = cv2.medianBlur(img, 21).astype(np.float32)
    return cv2.GaussianBlur(m, (0, 0), 6)


def hybride(ref, al, Z):
    """Étiquettes : pixels d'origine x lumière lissée de l'IA. Ailleurs : rendu IA."""
    ratio = (basse_freq(al) + 3) / (basse_freq(ref) + 3)
    etiq = np.clip(ref.astype(np.float32) * np.clip(ratio, 0.5, 2.2), 0, 255)
    out = Z[..., None] * etiq + (1 - Z[..., None]) * al.astype(np.float32)
    return np.clip(out, 0, 255).round().astype(np.uint8)


def lumiere_code(rgb, M, Z, type_):
    """Éclairage studio par code seul : volume (gauche clair, droite dans l'ombre), reflets verticaux, liseré."""
    f = rgb.astype(np.float32) / 255
    H, W = M.shape
    u = np.full((H, W), -1, np.float32)
    for yy in range(H):
        r = np.nonzero(M[yy] > 0.5)[0]
        if len(r) > 4:
            u[yy, r[0]:r[-1] + 1] = np.linspace(0, 1, r[-1] - r[0] + 1)
    dedans = u >= 0
    vol = 0.86 + 0.20 * np.exp(-((u - 0.28) / 0.30) ** 2) - 0.16 * np.clip((u - 0.72) / 0.28, 0, 1) ** 2
    f = np.where(dedans[..., None], f * vol[..., None], f)
    if type_ in ('verre_clair', 'verre_sombre', 'pot'):
        spec = 0.55 * np.exp(-((u - 0.17) / 0.035) ** 2) + 0.22 * np.exp(-((u - 0.86) / 0.025) ** 2)
        spec = spec * (1 - 0.8 * Z) * dedans
        spec = cv2.GaussianBlur(spec.astype(np.float32), (0, 0), 1.5)
        f = 1 - (1 - f) * (1 - spec[..., None])
    return (np.clip(f, 0, 1) * 255).round().astype(np.uint8)


def traite_produit(k, p, cfg, args, rapport):
    a = nettoie_bords(charge(args.entree, p['fichier']))
    zone_incl = p.get('inclinaison_zone', (0.45, 0.93))
    ang = inclinaison(a, zone_incl)
    a = redresse(a, ang)
    a = etalonne(a, p.get('gains', [1, 1, 1]), p.get('gamma', 1.0))
    c = canevas_ia(a)
    ref, M = c['rgb'], c['M']
    boites = boites_px(p['zones'], c['boite'])
    Z = masque_zones(M.shape, boites)
    dos = Path(args.sortie) / 'ia'
    dos.mkdir(parents=True, exist_ok=True)
    Image.fromarray(ref).save(dos / f'{k}_entree.png')
    essais, choisi = [], None
    if args.ia:
        x0, y0, x1, y1 = max(boites, key=lambda b: (b[2] - b[0]) * (b[3] - b[1]))
        gp = Image.fromarray(ref[y0:y1, x0:x1])
        f = min(2.5, 1600 / max(gp.size))
        gp = gp.resize((int(gp.width * f), int(gp.height * f)), Image.LANCZOS)
        for i, (modele, taille) in enumerate(ESSAIS, 1):
            fic = dos / f'{k}_essai{i}.png'
            if fic.exists():
                out = Image.open(fic).convert('RGB')
            else:
                from packshot_ia import retouche
                print(f' {k} essai {i} ({modele} {taille})')
                out = retouche(Image.fromarray(ref), gp, fic, p['liquide'], args.journal, args.plafond,
                               modele=modele, taille=taille, format_=c['fmt'])
                if out is None:
                    break
            out = np.array(out.resize((ref.shape[1], ref.shape[0]), Image.LANCZOS))
            al, ecc = K.aligne(ref, out, M)
            Mi = masque_ia(al, c['fond'])
            ok, rap = K.controle(ref, al, M, Mi, boites)
            rap.update({'essai': i, 'modele': modele, 'ecc': round(ecc, 4)})
            essais.append((rap, al))
            print(f'  {k} essai {i} : {"ACCEPTÉ" if ok else "rejeté"} (tuiles rejetées {rap["tuiles_rejetees"]}, '
                  f'pire {rap["pire_tuile"]}, mots manquants {rap["mots_manquants"]}, IoU {rap["iou"]}, ECC {ecc:.3f})')
            if ok:
                choisi = ('ia', al)
                break
    if choisi is None:
        bons = [(r, al) for r, al in essais if r['iou'] >= K.SEUIL_IOU - 0.01 and r['ecc'] >= 0.9]
        if bons:
            r, al = max(bons, key=lambda t: t[0]['ecc'] + (0.02 if t[0]['modele'] == ESSAIS[0][0] else 0))
            choisi = ('hybride', hybride(ref, al, Z), r['essai'])
        else:
            choisi = ('code', lumiere_code(ref, M, Z, p['type']))
    res = choisi[1]
    ok, final = K.controle(ref, res, M, M, boites)
    mode = choisi[0]
    print(f' {k} -> {mode}{" (lumière de l’essai %d)" % choisi[2] if mode == "hybride" else ""} ; '
          f'contrôle final des lettres : {"OK" if ok else "ÉCHEC"} (pire tuile {final["pire_tuile"]}, '
          f'mots OCR {final["mots_ocr_lus"]}, manquants {final["mots_manquants"]})')
    if not ok:                                      # ultime sécurité : jamais d'étiquette douteuse
        res, mode = lumiere_code(ref, M, Z, p['type']), 'code'
        ok, final = K.controle(ref, res, M, M, boites)
    x0, y0, pw, ph = c['boite']
    rgba = np.dstack([res[y0:y0 + ph, x0:x0 + pw], (c['produit'][:, :, 3] * 255).round().astype(np.uint8)])
    Path(args.sortie, 'produits').mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba).save(Path(args.sortie, 'produits', f'{k}.png'))
    brut = np.dstack([ref[y0:y0 + ph, x0:x0 + pw], rgba[:, :, 3]])
    Image.fromarray(brut).save(Path(args.sortie, 'produits', f'{k}_brut.png'))
    rapport[k] = {'nom': p['nom'], 'inclinaison_corrigee_deg': round(ang, 2) if abs(ang) >= 0.3 else 0,
                  'mode': mode, 'essais_ia': [r for r, _ in essais], 'controle_final': final,
                  'zones_px_produit': [[b[0] - x0, b[1] - y0, b[2] - x0, b[3] - y0] for b in boites]}


# ---------------------------------------------------------------- composition
def colle(fond, rgba, x, y, opacite=1.0):
    """Colle rgba (float 0-1) en (x, y) sur fond (float 0-255), avec découpe aux bords du canevas."""
    H, W = fond.shape[:2]
    h, w = rgba.shape[:2]
    ax0, ay0, ax1, ay1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if ax0 >= ax1 or ay0 >= ay1:
        return
    p = rgba[ay0 - y:ay1 - y, ax0 - x:ax1 - x]
    al = p[:, :, 3:] * opacite
    fond[ay0:ay1, ax0:ax1] = p[:, :, :3] * 255 * al + fond[ay0:ay1, ax0:ax1] * (1 - al)


def reflet(rgba, force=0.32, longueur=0.28):
    r = rgba[::-1].copy()
    h = r.shape[0]
    d = np.arange(h, dtype=np.float32)[:, None] / h
    net = r.copy()
    flou = cv2.GaussianBlur(r, (0, 0), max(2.0, h / 160))
    mix = np.clip(d / 0.25, 0, 1)[..., None]
    r = net * (1 - mix) + flou * mix
    r[:, :, :3] *= np.array([0.80, 0.70, 0.74], np.float32)
    r[:, :, 3] *= force * np.exp(-d[:, 0:1].repeat(r.shape[1], 1) / longueur)[:, :] * 1.0
    return r


def ombre(fond, xc, yb, largeur):
    H, W = fond.shape[:2]
    calque = np.zeros((H, W), np.float32)
    cv2.ellipse(calque, (int(xc), int(yb)), (int(largeur * 0.52), max(5, int(largeur * 0.05))), 0, 0, 360, 1, -1)
    large = cv2.GaussianBlur(calque, (0, 0), largeur * 0.12)
    serre = cv2.GaussianBlur(calque, (0, 0), 3)
    a = np.clip(0.55 * serre + 0.45 * large, 0, 0.85)[..., None]
    fond *= 1 - a


def liseré(rgba, force=0.30):
    """Liseré chaud sur les contours gauche et droit (contre-jour), identique pour tous les produits."""
    al = (rgba[:, :, 3] > 0.5).astype(np.uint8)
    d = cv2.distanceTransform(al, cv2.DIST_L2, 3)
    ep = max(2.0, rgba.shape[1] / 140)
    bord = np.exp(-d / ep) * al
    gx = cv2.Sobel(cv2.GaussianBlur(al.astype(np.float32), (0, 0), 3), cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(cv2.GaussianBlur(al.astype(np.float32), (0, 0), 3), cv2.CV_32F, 0, 1)
    cote = np.abs(gx) / (np.abs(gx) + np.abs(gy) + 1e-4)
    s = (bord * cote * force)[..., None]
    rgb = 1 - (1 - rgba[:, :, :3]) * (1 - s * np.array([1.0, 0.78, 0.6], np.float32))
    return np.dstack([rgb, rgba[:, :, 3]])


def spot(rgba, zones, force=0.09):
    """Spot dédié au produit vedette : étiquette un peu plus lumineuse, centre plus fort."""
    h, w = rgba.shape[:2]
    S = np.zeros((h, w), np.float32)
    for z in zones:
        x0, y0, x1, y1 = int(z[0] * w), int(z[1] * h), int(z[2] * w), int(z[3] * h)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        cx, cy = (x0 + x1) / 2 - 0.08 * w, (y0 + y1) / 2
        S[y0:y1, x0:x1] = np.exp(-(((xx - cx) / (0.9 * w)) ** 2 + ((yy - cy) / (1.2 * (y1 - y0))) ** 2))
    S = cv2.GaussianBlur(S, (0, 0), w / 30)
    rgb = np.clip(rgba[:, :, :3] * (1 + force * S[..., None]), 0, 1)
    return np.dstack([rgb, rgba[:, :, 3]])


def compose(cfg, fond_png, dossier_produits, rapport, suffixe='', brut=False):
    fond = np.array(Image.open(fond_png).convert('RGB')).astype(np.float32)
    W = fond.shape[1]
    P = {}
    for k in cfg['ordre'] + [d['id'] for d in cfg['devant']]:
        f = Path(dossier_produits, f'{k}_brut.png' if brut else f'{k}.png')
        P[k] = np.array(Image.open(f).convert('RGBA')).astype(np.float32) / 255
    cm = lambda k: cfg['produits'][k]['hauteur_cm'] * P[k].shape[1] / P[k].shape[0]
    total = sum(cm(k) for k in cfg['ordre']) + cfg['ecart_cm'] * (len(cfg['ordre']) - 1)
    ppc = (W - 2 * cfg['marge_laterale']) / total
    x, pos = 0.0, {}
    for k in cfg['ordre']:
        pos[k] = (x, x + cm(k) * ppc)
        x += cm(k) * ppc + cfg['ecart_cm'] * ppc
    v = cfg['vedette']
    decal = W / 2 - (pos[v][0] + pos[v][1]) / 2           # le produit vedette au centre exact
    decal = min(max(decal, 80 - pos[cfg['ordre'][0]][0]), W - 80 - pos[cfg['ordre'][-1]][1])
    pos = {k: (a + decal, b + decal) for k, (a, b) in pos.items()}
    calques = []
    for k in cfg['ordre']:
        h = int(round(cfg['produits'][k]['hauteur_cm'] * ppc))
        w = int(round(pos[k][1] - pos[k][0]))
        calques.append((k, int(round(pos[k][0])), cfg['ligne_bouteilles'] - h, w, h))
    for d in cfg['devant']:
        k = d['id']
        g, dr = d['entre']
        xc = (pos[g][1] + pos[dr][0]) / 2
        h = int(round(cfg['produits'][k]['hauteur_cm'] * ppc * cfg['echelle_pots']))
        w = int(round(h * P[k].shape[1] / P[k].shape[0]))
        calques.append((k, int(round(xc - w / 2)), cfg['ligne_pots'] - h, w, h))
    occupation = np.zeros(fond.shape[:2], np.int16) - 1
    places = {}
    for i, (k, x0, y0, w, h) in enumerate(calques):
        p = cv2.resize(P[k], (w, h), interpolation=cv2.INTER_AREA)
        p = np.clip(p, 0, 1)
        if not brut:
            p = liseré(p)
            if k == v:
                p = spot(p, cfg['produits'][k]['zones'])
        colle(fond, reflet(p), x0, y0 + h)
        ombre(fond, x0 + w / 2, y0 + h, w)
        colle(fond, p, x0, y0)
        m = p[:, :, 3] > 0.5
        sub = occupation[y0:y0 + h, x0:x0 + w]
        sub[m] = i
        places[k] = (x0, y0, w, h)
    # contrôle : aucune zone d'étiquette recouverte par un autre produit
    caches = {}
    for i, (k, x0, y0, w, h) in enumerate(calques):
        for z in cfg['produits'][k]['zones']:
            zx0, zy0, zx1, zy1 = int(x0 + z[0] * w), int(y0 + z[1] * h), int(x0 + z[2] * w), int(y0 + z[3] * h)
            sub = occupation[zy0:zy1, zx0:zx1]
            autres = (sub >= 0) & (sub != i)
            if autres.any():
                caches[k] = int(autres.sum())
    img = np.clip(fond, 0, 255).round().astype(np.uint8)
    if not brut:
        rapport['_composition'] = {'pixels_par_cm': round(ppc, 2), 'places': places,
                                   'etiquettes_masquees': caches or 'aucune'}
    return Image.fromarray(img), places, ppc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--entree', default='bouteilles-gemini/detoures')
    ap.add_argument('--sortie', default='studio/sortie')
    ap.add_argument('--config', default='studio/config.json')
    ap.add_argument('--fond', default='studio/background.png')
    ap.add_argument('--ia', action='store_true', help='retouche IA par produit (sinon : éclairage par code)')
    ap.add_argument('--journal', default='bouteilles-gemini/api-essais/depenses.csv')
    ap.add_argument('--plafond', type=float, default=4.8)
    ap.add_argument('--seulement', default='', help='numéros de produits à (re)traiter, ex. 06,04')
    ap.add_argument('--compose-seulement', action='store_true')
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding='utf-8'))
    sortie = Path(a.sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    if not Path(a.fond).exists():                    # créé une seule fois, jamais modifié ensuite
        cree_fond(cfg, a.fond)
    f_rap = sortie / 'rapport.json'
    rapport = json.loads(f_rap.read_text(encoding='utf-8')) if f_rap.exists() else {}
    if not a.compose_seulement:
        liste = a.seulement.split(',') if a.seulement else list(cfg['produits'])
        for k in liste:
            traite_produit(k, cfg['produits'][k], cfg, a, rapport)
    img, places, ppc = compose(cfg, a.fond, sortie / 'produits', rapport)
    img.save(sortie / 'visuel_cave71_A1.png')
    w = img.copy()
    w.thumbnail((1600, 1600 * 2))
    w.convert('RGB').save(sortie / 'visuel_cave71_A1_web.jpg', quality=86, optimize=True)
    avant, _, _ = compose(cfg, a.fond, sortie / 'produits', rapport, brut=True)
    avant.save(sortie / 'avant_sans_retouche.png')
    f_rap.write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')
    print('composition :', rapport['_composition']['etiquettes_masquees'], '| px/cm', round(ppc, 2))


if __name__ == '__main__':
    main()
