"""Maquette de la photo de groupe (trois plans, esprit v8) avec les VRAIS produits détourés.

Elle sert de base à la génération (le modèle la refait en vraie photo de studio en gardant les places), puis
de repère au recollage des vraies étiquettes (positions exactes + parties visibles de chaque produit).

Usage (depuis panneau/) :
    python3 tools/base_groupe.py studio/groupe.json studio/config.json studio/groupe/
Sorties : base.jpg, placement.json, visible_NN.png (parties de chaque produit non cachées par un autre).
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

DETOURES = Path('bouteilles-gemini/detoures')


def fond(W, H, horizon):
    y = np.arange(H, dtype=np.float32)[:, None]
    x = np.arange(W, dtype=np.float32)[None, :]
    noir, lie, coeur = np.array([12, 4, 7.]), np.array([48, 14, 24.]), np.array([92, 32, 38.])
    halo = np.exp(-(((x - W / 2) / (W * 0.42)) ** 2 + ((y - horizon * 0.55) / (H * 0.55)) ** 2))
    mur = noir + (lie - noir) * halo[..., None] + (coeur - lie) * (halo ** 3)[..., None]
    d = np.clip(y - horizon, 0, None)
    sol = noir * 0.7 + mur[np.clip((horizon - d * 1.5).astype(int), 0, H - 1)[:, 0]] * (0.22 * np.exp(-d / 260))[..., None]
    t = np.clip((y - horizon + 4) / 8, 0, 1)[..., None]
    return mur * (1 - t) + sol * t


def largeur(cfg, k, px_cm):
    im = Image.open(DETOURES / cfg['produits'][k]['fichier'])
    a = np.array(im.convert('RGBA'))[:, :, 3]
    ys, xs = np.nonzero(a > 12)
    return cfg['produits'][k]['hauteur_cm'] * px_cm * (xs.max() - xs.min() + 1) / (ys.max() - ys.min() + 1)


def place_rangee(g, cfg):
    """x de chaque produit de la rangée : voisins collés, léger chevauchement entre profondeurs
    différentes ; rangée recentrée sur le produit vedette ; pots centrés devant le produit indiqué."""
    W = g['canevas'][0]
    xs, x = {}, 0.0
    prec = None
    for k, plan in g['rangee']:
        w = largeur(cfg, k, g['plans'][plan]['px_cm'])
        if prec is not None:
            x -= g['chevauchement'] if plan != prec else -g['espace_meme_plan']
        xs[k] = x + w / 2
        x += w
        prec = plan
    decal = W / 2 - xs[g['vedette']]
    out = [{'id': k, 'plan': plan, 'x': xs[k] + decal} for k, plan in g['rangee']]
    gauche = min(o['x'] - largeur(cfg, o['id'], g['plans'][o['plan']]['px_cm']) / 2 for o in out)
    droite = max(o['x'] + largeur(cfg, o['id'], g['plans'][o['plan']]['px_cm']) / 2 for o in out)
    print(f'rangée : de {gauche:.0f} à {droite:.0f} px (canevas {W})')
    # ordre de dessin : fond, milieu, devant
    rang = {'fond': 0, 'milieu': 1, 'devant': 2}
    out.sort(key=lambda o: rang[o['plan']])
    for k, devant_de in g.get('pots', []):
        out.append({'id': k, 'plan': 'devant', 'x': xs[devant_de] + decal})
    return out


def main():
    g = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    cfg = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
    out = Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    W, H = g['canevas']
    horizon = min(p['base'] for p in g['plans'].values()) - 90
    img = fond(W, H, horizon)
    occ = np.full((H, W), -1, np.int16)
    placement, formes = {}, {}
    produits = g.get('produits') or place_rangee(g, cfg)
    for i, e in enumerate(produits):
        k = e['id']
        pl = g['plans'][e['plan']]
        im = np.array(Image.open(DETOURES / cfg['produits'][k]['fichier']).convert('RGBA'))
        ys, xs = np.nonzero(im[:, :, 3] > 12)
        im = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        h = int(round(cfg['produits'][k]['hauteur_cm'] * pl['px_cm']))
        s = h / im.shape[0]
        w = int(round(im.shape[1] * s))
        p = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        x0, y0 = int(round(e['x'] - w / 2)), pl['base'] - h
        # reflet et ombre de contact, pour que le modèle comprenne où chaque produit est posé
        r = p[::-1].copy()
        r[:, :, 3] *= 0.28 * np.exp(-np.arange(h)[:, None] / (0.22 * h))
        r = cv2.GaussianBlur(r, (0, 0), 2)
        for (q, yy) in ((r, pl['base']), (p, y0)):
            a0, b0 = max(0, yy), min(H, yy + h)
            c0, d0 = max(0, x0), min(W, x0 + w)
            if a0 >= b0 or c0 >= d0:
                continue
            sub = q[a0 - yy:b0 - yy, c0 - x0:d0 - x0]
            if q is p:
                ombre = np.zeros((H, W), np.float32)
                cv2.ellipse(ombre, (x0 + w // 2, pl['base']), (int(w * 0.5), max(4, int(w * 0.05))), 0, 0, 360, 1, -1)
                ombre = cv2.GaussianBlur(ombre, (0, 0), w * 0.08)
                img *= 1 - 0.75 * np.clip(ombre, 0, 1)[..., None]
                vis = sub[:, :, 3] > 0.5
                occ[a0:b0, c0:d0][vis] = i
                forme = np.zeros((H, W), bool)
                forme[a0:b0, c0:d0] = vis
                formes[k] = forme
            al = sub[:, :, 3:]
            img[a0:b0, c0:d0] = sub[:, :, :3] * 255 * al + img[a0:b0, c0:d0] * (1 - al)
        placement[k] = {'x0': x0, 'y0': y0, 'w': w, 'h': h, 'echelle': s, 'ordre': i, 'plan': e['plan']}
    for k, v in placement.items():
        Image.fromarray(((occ == v['ordre']) * 255).astype(np.uint8)).save(out / f'visible_{k}.png')
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out / 'base.jpg', quality=94)
    (out / 'placement.json').write_text(json.dumps(placement, indent=1))
    # étiquettes cachées par un produit placé devant (part de la zone d'étiquette principale)
    for k, v in placement.items():
        z = cfg['produits'][k]['zones'][0]
        zx0, zy0 = v['x0'] + int(z[0] * v['w']), v['y0'] + int(z[1] * v['h'])
        zx1, zy1 = v['x0'] + int(z[2] * v['w']), v['y0'] + int(z[3] * v['h'])
        f = formes[k][zy0:zy1, zx0:zx1]
        autre = (occ[zy0:zy1, zx0:zx1][f] != v['ordre']).mean() if f.any() else 0
        if autre > 0.005:
            print(f'{k} : {autre:.0%} de l’étiquette cachée')
    print('maquette :', out / 'base.jpg')


if __name__ == '__main__':
    main()
