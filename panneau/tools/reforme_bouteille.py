"""Redonne à une bouteille de la photo IA la vraie forme du produit (col, épaules, capsule) sans changer
la lumière de la scène.

Principe : on prend la silhouette du vrai produit (photo de référence, mise à l'échelle sur la largeur du
corps de la bouteille de la scène) et, ligne par ligne, on rééchantillonne horizontalement le verre de la
bouteille IA (avec ses reflets) pour qu'il remplisse la nouvelle silhouette. Seule la partie haute change
(au-dessus de la ligne LIMITE, où les deux bouteilles ont la même largeur de corps). Le fond laissé à nu
par l'ancienne forme est reconstruit par inpainting à partir du mur autour.

Usage (depuis panneau/) :
    python3 tools/reforme_bouteille.py scene.jpg sortie.jpg reference.jpg MODE X0 Y0 X1 Y1 LIMITE ANCRE_REF ANCRE_SCENE CAPSULE_SCENE
      MODE        : 'blanc' (référence sur fond blanc, seuil) ou 'detour' (détourage rembg)
      X0..Y1      : boîte autour de la bouteille de la scène (sans les voisines si possible)
      LIMITE      : ligne de la scène sous laquelle rien ne change (début du corps cylindrique)
      ANCRE_REF / ANCRE_SCENE : une ligne de la référence et la ligne correspondante dans la scène
                    (ex. le bas de la bouteille, ou le haut de l'étiquette)
      CAPSULE_SCENE : ligne du bas de la capsule de l'ancienne bouteille (pour garder une capsule nette)
      Variable ANCIENNE_BORDS="y:g:d,..." : bords de l'ancienne bouteille relevés à la main (fiable).
      Variable ANCIENNE=ambre : silhouette de l'ancienne bouteille par la couleur du verre ambré (bière)
                    au lieu du détourage rembg.
      [ECHELLE_V] : échelle verticale imposée, quand la bouteille de la scène est plus trapue que la vraie
                    et que la vraie forme ne tiendrait pas dans le cadre
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image


def masque_ref(ref, mode):
    if mode == 'blanc':
        L = cv2.cvtColor(ref, cv2.COLOR_RGB2GRAY)
        m = (L < 232).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    else:
        from rembg import new_session, remove
        a = np.array(remove(Image.fromarray(ref), session=new_session('isnet-general-use')))[..., 3]
        m = (a > 128).astype(np.uint8)
    # étiquette blanche, reflets : on remplit chaque ligne entre ses bords extrêmes
    for y in range(m.shape[0]):
        xs = np.where(m[y])[0]
        if len(xs):
            m[y, xs[0]:xs[-1] + 1] = 1
    return m


def plage(row, cx):
    """Étendue [g, d] du segment de pixels à 1 qui contient (ou est le plus proche de) la colonne cx."""
    xs = np.where(row)[0]
    if not len(xs):
        return None
    # segments contigus
    coupures = np.where(np.diff(xs) > 1)[0]
    debuts = np.r_[xs[0], xs[coupures + 1]]
    fins = np.r_[xs[coupures], xs[-1]]
    for g, d in zip(debuts, fins):
        if g <= cx <= d:
            return g, d
    k = np.argmin(np.minimum(abs(debuts - cx), abs(fins - cx)))
    return debuts[k], fins[k]


def main():
    scene_p, sortie, ref_p, mode = sys.argv[1:5]
    X0, Y0, X1, Y1, LIM, ancre_ref, ancre_sc, cap_sc = map(int, sys.argv[5:13])
    kv_force = float(sys.argv[13]) if len(sys.argv) > 13 else None  # échelle verticale imposée (sinon = horizontale)
    img = np.array(Image.open(scene_p).convert('RGB'))
    ref = np.array(Image.open(ref_p).convert('RGB'))
    H, W = img.shape[:2]

    # 1. silhouette de l'ancienne bouteille (détourage de la boîte, segment central de chaque ligne)
    crop = img[Y0:Y1, X0:X1]
    if os.environ.get('ANCIENNE_BORDS'):
        # bords relevés à la main : "y:gauche:droite,..." interpolés ligne par ligne
        cles = sorted(tuple(map(int, c.split(':'))) for c in os.environ['ANCIENNE_BORDS'].split(','))
        a = np.zeros(crop.shape[:2], bool)
        cy = [c[0] for c in cles]
        for y in range(cles[0][0], cles[-1][0] + 1):
            gl = np.interp(y, cy, [c[1] for c in cles])
            dr = np.interp(y, cy, [c[2] for c in cles])
            a[y - Y0, int(round(gl)) - X0:int(round(dr)) - X0 + 1] = True
    elif os.environ.get('ANCIENNE') == 'ambre':
        # verre ambré (bleu bien plus faible que le vert) ou reflet clair, contre un mur lie-de-vin (B ~ G)
        c = crop.astype(int)
        a = ((c[..., 1] - c[..., 2]) > 8) | (c.min(axis=2) > 100)
        a = cv2.morphologyEx(a.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 11), np.uint8)).astype(bool)
    else:
        from rembg import new_session, remove
        a = np.array(remove(Image.fromarray(crop), session=new_session('isnet-general-use')))[..., 3] > 128
    cx_old = (X1 - X0) // 2
    ancienne = np.zeros((H, W), bool)
    spans_old = {}
    for y in range(Y0, Y1):
        p = plage(a[y - Y0], cx_old)
        if p:
            spans_old[y] = (p[0] + X0, p[1] + X0)
            ancienne[y, p[0] + X0:p[1] + X0 + 1] = True
    haut_old = min(spans_old)

    # 2. silhouette du vrai produit, mise à l'échelle sur la largeur du corps à la ligne LIMITE
    mr = masque_ref(ref, mode)
    ys = np.where(mr.any(axis=1))[0]
    cxr = int(np.median(np.where(mr[ys[len(ys) * 3 // 4]])[0]))
    larg_ref = []
    for y in range(ys[0], ys[-1] + 1):
        p = plage(mr[y], cxr)
        larg_ref.append(p[1] - p[0] + 1 if p else 0)
    n = len(larg_ref)
    corps_ref = np.median(larg_ref[int(n * 0.45):int(n * 0.75)])  # corps, hors bas (main, table…)
    g, d = spans_old[LIM]
    corps_sc = d - g + 1
    k = corps_sc / corps_ref
    centre_sc = (g + d) / 2
    # ligne de la référence qui tombe sur la ligne y de la scène
    kv = kv_force or k

    def y_ref(y):
        return ancre_ref + (y - ancre_sc) / kv
    nouvelle = np.zeros((H, W), bool)
    spans_new = {}
    haut_new = None
    for y in range(0, LIM):
        yr = int(round(y_ref(y)))
        if yr < ys[0] or yr > ys[-1]:
            continue
        p = plage(mr[yr], cxr)
        if not p:
            continue
        gl = centre_sc + (p[0] - cxr) * k
        dr = centre_sc + (p[1] - cxr) * k
        spans_new[y] = (gl, dr)
        nouvelle[y, int(round(gl)):int(round(dr)) + 1] = True
        haut_new = y if haut_new is None else haut_new
    # bords lissés d'une ligne à l'autre (le masque de la référence est un peu crénelé)
    lignes = sorted(spans_new)
    if len(lignes) > 7:
        G = np.convolve(np.pad([spans_new[y][0] for y in lignes], 3, mode='edge'), np.ones(7) / 7, 'valid')
        D = np.convolve(np.pad([spans_new[y][1] for y in lignes], 3, mode='edge'), np.ones(7) / 7, 'valid')
        nouvelle[:] = False
        for y, gl, dr in zip(lignes, G, D):
            spans_new[y] = (gl, dr)
            nouvelle[y, int(round(gl)):int(round(dr)) + 1] = True
    for y in range(LIM, Y1):          # sous la limite : forme inchangée
        if y in spans_old:
            spans_new[y] = spans_old[y]
            nouvelle[y, spans_old[y][0]:spans_old[y][1] + 1] = True

    # capsule : même hauteur en pixels que l'ancienne (les capsules ont la même taille)
    cap_new = haut_new + (cap_sc - haut_old)

    # 3. correspondance verticale ancienne -> nouvelle : [haut, capsule, LIMITE]
    def y_old(y):
        if y <= cap_new:
            t = (y - haut_new) / max(1e-6, cap_new - haut_new)
            return haut_old + t * (cap_sc - haut_old)
        t = (y - cap_new) / max(1e-6, LIM - cap_new)
        return cap_sc + t * (LIM - cap_sc)

    # 4. plaque de fond : l'ancienne bouteille (au-dessus de LIMITE) effacée par inpainting
    zone = np.zeros((H, W), np.uint8)
    zone[:LIM][ancienne[:LIM]] = 255
    zone = cv2.dilate(zone, np.ones((5, 5), np.uint8), iterations=2)
    zone[LIM:] = 0
    fond = cv2.inpaint(img, zone, 12, cv2.INPAINT_TELEA)
    fond = np.where(zone[..., None] > 0, cv2.GaussianBlur(fond, (0, 0), 3), img)

    # 5. nouvelle bouteille : rééchantillonnage ligne par ligne du verre de l'ancienne
    mapx = np.zeros((H, W), np.float32)
    mapy = np.zeros((H, W), np.float32)
    for y, (gl, dr) in spans_new.items():
        if y >= LIM:
            continue
        yo = y_old(y)
        yo_i = int(round(min(max(yo, haut_old), LIM - 1)))
        while yo_i not in spans_old and yo_i < LIM:
            yo_i += 1
        og, od = spans_old[yo_i]
        xs = np.arange(int(np.floor(gl)), int(np.ceil(dr)) + 1)
        t = (xs - gl) / max(1e-6, dr - gl)
        mapx[y, xs] = og + t * (od - og)
        mapy[y, xs] = yo
    warp = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)
    # adoucit les petites marches d'une ligne à l'autre (reflets verticaux du verre)
    warp = cv2.GaussianBlur(warp, (0, 0), sigmaX=0.4, sigmaY=1.4)
    m = np.zeros((H, W), np.float32)
    m[:LIM][nouvelle[:LIM]] = 1
    m = cv2.GaussianBlur(m, (0, 0), 0.6)
    m[LIM:] = 0
    out = fond * (1 - m[..., None]) + warp * m[..., None]
    out[LIM:] = img[LIM:]
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(sortie, quality=95)
    print('corps ref', corps_ref, 'corps scene', corps_sc)
    print(sortie, 'haut', haut_old, '->', haut_new, 'capsule', cap_sc, '->', round(cap_new), 'échelle', round(k, 3))


if __name__ == '__main__':
    main()
