"""Recolle les VRAIES étiquettes sur une photo de groupe générée (essai 2), en gardant la lumière de la scène.

Pour chaque zone d'étiquette (studio/config.json, en fraction du produit détouré d'origine) :
  1. repérage approximatif : la zone est cherchée dans le montage de départ (base_montage_16x9.jpg), qui a
     servi de modèle à la génération, donc la même place à quelques pixels près ;
  2. recalage fin sur la photo générée : points SIFT + RANSAC (homographie), puis ECC ;
  3. transfert : pixels de la vraie étiquette x lumière lissée de la photo (médiane + flou : les lettres
     inventées disparaissent de cette lumière, il ne reste que l'éclairage, les reflets larges, l'ombre) ;
  4. contrôle : la structure fine (lettres) du résultat est comparée à la vraie étiquette, tuile par tuile.

Usage (depuis panneau/) :
    python3 tools/recolle_scene.py photo.png base_montage.jpg sortie.png [--seulement 06] [--debug dossier]
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import packshot_controle as K  # noqa: E402

DETOURES = Path('bouteilles-gemini/detoures')
# montage d'origine (tools/compose_produits.py) : 40 px par cm, puis remis en 16:9 et réduit à 2752 px
ECHELLE_BASE = 40 * 2752 / 4142


def gris(a):
    return cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)


def trouve_dans_base(base_g, tpl_g):
    r = cv2.matchTemplate(base_g, tpl_g, cv2.TM_CCOEFF_NORMED)
    _, v, _, loc = cv2.minMaxLoc(r)
    return loc, v


def homographie_sift(src_g, dst_g, H0):
    """Homographie src -> dst, initialisée par H0 ; SIFT + RANSAC puis affinage ECC."""
    sift = cv2.SIFT_create(nfeatures=4000)
    k1, d1 = sift.detectAndCompute(src_g, None)
    k2, d2 = sift.detectAndCompute(dst_g, None)
    H = H0.copy()
    n_in = 0
    if d1 is not None and d2 is not None and len(k1) > 8 and len(k2) > 8:
        m = cv2.BFMatcher(cv2.NORM_L2).knnMatch(d1, d2, k=2)
        bons = [a for a, b in (x for x in m if len(x) == 2) if a.distance < 0.78 * b.distance]
        # on ne garde que les paires cohérentes avec la position attendue (H0)
        if len(bons) >= 8:
            p1 = np.float32([k1[x.queryIdx].pt for x in bons])
            p2 = np.float32([k2[x.trainIdx].pt for x in bons])
            att = cv2.perspectiveTransform(p1[None], H0)[0]
            proche = np.linalg.norm(att - p2, axis=1) < 0.08 * max(dst_g.shape)
            if proche.sum() >= 8:
                Hs, inl = cv2.findHomography(p1[proche], p2[proche], cv2.RANSAC, 3.0)
                if Hs is not None:
                    n_in = int(inl.sum())
                    if n_in >= 10:
                        H = Hs
    # affinage ECC sur les gradients (insensible aux écarts de lumière)
    def grad(g):
        g = cv2.GaussianBlur(g.astype(np.float32) / 255, (0, 0), 1.0)
        return cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
    a = cv2.warpPerspective(grad(src_g), H, dst_g.shape[::-1])
    msk = cv2.warpPerspective(np.ones_like(src_g, np.uint8), H, dst_g.shape[::-1])
    msk = cv2.erode(msk, np.ones((7, 7), np.uint8))
    W = np.eye(3, dtype=np.float32)
    cc = 0.0
    try:
        cc, W = cv2.findTransformECC(grad(dst_g), a, W, cv2.MOTION_HOMOGRAPHY,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-7), msk, 1)
        H = np.linalg.inv(W) @ H
    except cv2.error:
        pass
    H = H / H[2, 2]
    # garde-fou : la zone recalée doit rester près de sa place connue (coins à moins de 5 % de la taille)
    h, w = src_g.shape
    coins = np.float32([[0, 0], [w, 0], [w, h], [0, h]])[None]
    c0, c1 = cv2.perspectiveTransform(coins, H0)[0], cv2.perspectiveTransform(coins, H)[0]
    taille = max(np.ptp(c0[:, 0]), np.ptp(c0[:, 1]))
    if np.abs(c1 - c0).max() > 0.05 * taille + 12:
        return H0.copy(), n_in, -1.0
    return H, n_in, float(cc)


def basse_freq(img, k=15, s=5):
    return cv2.GaussianBlur(cv2.medianBlur(img, k).astype(np.float32), (0, 0), s)


def recolle_zone(photo, src_rgb, src_a, H, retrait=0.0, flou_bord=3, lissage=(15, 5)):
    """Pose la zone source (déjà découpée) sur la photo via H, avec la lumière de la photo."""
    h, w = photo.shape[:2]
    sh, sw = src_rgb.shape[:2]
    m = src_a.copy()
    if retrait:
        r = int(retrait * sw)
        m[:, :r] = 0
        m[:, sw - r:] = 0
    vrai = cv2.warpPerspective(src_rgb, H, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    M = cv2.warpPerspective(m, H, (w, h), flags=cv2.INTER_LINEAR)
    M = cv2.GaussianBlur(cv2.erode(M, np.ones((3, 3), np.uint8)), (0, 0), flou_bord)
    k, s = lissage
    ratio = (basse_freq(photo, k, s) + 4) / (basse_freq(vrai, k, s) + 4)
    eclaire = np.clip(vrai.astype(np.float32) * np.clip(ratio, 0.35, 2.5), 0, 255)
    out = M[..., None] * eclaire + (1 - M[..., None]) * photo.astype(np.float32)
    return np.clip(out, 0, 255).round().astype(np.uint8), vrai, M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('photo')
    ap.add_argument('base')
    ap.add_argument('sortie')
    ap.add_argument('--config', default='studio/config.json')
    ap.add_argument('--reglages', default='studio/recollage.json')
    ap.add_argument('--seulement', default='')
    ap.add_argument('--debug', default='')
    ap.add_argument('--placement', default='', help='placement.json de tools/base_groupe.py (positions exactes)')
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text(encoding='utf-8'))
    regl = json.loads(Path(a.reglages).read_text(encoding='utf-8')) if Path(a.reglages).exists() else {}
    place = json.loads(Path(a.placement).read_text()) if a.placement else {}
    photo = np.array(Image.open(a.photo).convert('RGB'))
    base = np.array(Image.open(a.base).convert('RGB').resize(photo.shape[1::-1], Image.LANCZOS))
    base_g, photo_g = gris(base), gris(photo)
    rapport = {}
    liste = a.seulement.split(',') if a.seulement else list(cfg['produits'])
    if place:     # du fond vers l'avant : un produit placé devant repasse par-dessus
        liste.sort(key=lambda k: place[k]['ordre'])
    for k in liste:
        p = cfg['produits'][k]
        r = regl.get(k, {})
        im = np.array(Image.open(DETOURES / p['fichier']).convert('RGBA'))
        ys, xs = np.nonzero(im[:, :, 3] > 12)
        im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        Hh, Ww = im.shape[:2]
        s_base = p['hauteur_cm'] * ECHELLE_BASE / Hh
        for iz, z in enumerate(r.get('zones', p['zones'])):
            x0, y0, x1, y1 = int(z[0] * Ww), int(z[1] * Hh), int(z[2] * Ww), int(z[3] * Hh)
            src = im[y0:y1, x0:x1]
            src_rgb, src_a = src[:, :, :3].copy(), src[:, :, 3].astype(np.float32) / 255
            if k in place:              # position exacte dans la maquette
                q = place[k]
                sb = q['echelle']
                H0 = np.array([[sb, 0, q['x0'] + x0 * sb], [0, sb, q['y0'] + y0 * sb], [0, 0, 1]], np.float64)
                v = 1.0
                vis = np.array(Image.open(Path(a.placement).parent / f'visible_{k}.png')) > 127
                # parties cachées par un produit placé devant : on n'y touche pas
                src_a = src_a * (cv2.warpPerspective(vis.astype(np.float32), np.linalg.inv(H0),
                                                     (src_a.shape[1], src_a.shape[0])) > 0.5)
            else:
                tpl = cv2.resize(gris(src_rgb), None, fx=s_base, fy=s_base, interpolation=cv2.INTER_AREA)
                (bx, by), v = trouve_dans_base(base_g, tpl)
                H0 = np.array([[s_base, 0, bx], [0, s_base, by], [0, 0, 1]], np.float64)
            H, n_in, cc = homographie_sift(gris(src_rgb), photo_g, H0)
            photo, vrai, M = recolle_zone(photo, src_rgb, src_a, H, retrait=r.get('retrait', 0.0),
                                          lissage=tuple(r.get('lissage', (15, 5))))
            # contrôle des lettres : résultat comparé à la vraie étiquette posée au même endroit
            ys2, xs2 = np.nonzero(M > 0.9)
            boite = (int(xs2.min()), int(ys2.min()), int(xs2.max()), int(ys2.max())) if len(xs2) else (0, 0, 1, 1)
            t = K.tuiles_texte(vrai, photo, boite)
            pire = min([x[0] for x in t], default=1.0)
            rapport[f'{k}.{iz}'] = {'nom': p['nom'], 'repere_base': round(float(v), 3), 'points_sift': n_in,
                                   'ecc': round(cc, 3), 'tuiles': len(t), 'pire_tuile': round(pire, 3),
                                   'boite': boite}
            print(f'{k}.{iz} {p["nom"][:40]:40s} repère {v:.2f}  SIFT {n_in:4d}  ECC {cc:.3f}  '
                  f'lettres : pire tuile {pire:.3f} sur {len(t)}')
            if a.debug:
                Path(a.debug).mkdir(parents=True, exist_ok=True)
                x0b, y0b, x1b, y1b = boite
                pad = 30
                c = photo[max(0, y0b - pad):y1b + pad, max(0, x0b - pad):x1b + pad]
                Image.fromarray(c).save(Path(a.debug, f'{k}_{iz}.png'))
    Image.fromarray(photo).save(a.sortie)
    Path(a.sortie).with_suffix('.json').write_text(json.dumps(rapport, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
