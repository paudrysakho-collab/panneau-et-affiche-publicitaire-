"""Pose un produit détouré (PNG transparent) au premier plan d'une photo studio.

- agrandit si besoin le bas de la photo (prolongement de la surface) pour laisser la place ;
- accorde la couleur du produit à une zone de référence de la photo (ex. l'étiquette du même produit
  rendue par l'IA), puis assombrit légèrement son côté droit (lumière venant de la gauche) ;
- ajoute une ombre de contact et un léger reflet sur la surface brillante.

Usage (depuis panneau/) :
    python3 tools/ajoute_produit.py entree.jpg sortie.jpg produit.png CX HAUT LARGEUR
        [--etendre-bas N] [--ref X0 Y0 X1 Y1 RX0 RY0 RX1 RY1]
    --ref : zone de la photo (X0..Y1) dont la couleur sert de cible, et zone correspondante du produit
            détouré, en fractions de sa taille (RX0..RY1, entre 0 et 1).
"""
import argparse

import cv2
import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('entree')
    ap.add_argument('sortie')
    ap.add_argument('produit')
    ap.add_argument('cx', type=float)
    ap.add_argument('haut', type=float)
    ap.add_argument('largeur', type=float)
    ap.add_argument('--etendre-bas', type=int, default=0)
    ap.add_argument('--ref', type=float, nargs=8)
    a = ap.parse_args()

    img = np.array(Image.open(a.entree).convert('RGB')).astype(np.float32)
    H, W = img.shape[:2]

    # 1. prolongement de la surface vers le bas : dernière bande lissée, qui s'assombrit doucement
    if a.etendre_bas:
        n = a.etendre_bas
        bande = cv2.GaussianBlur(img[H - 6:H].mean(axis=0, keepdims=True), (0, 0), sigmaX=6, sigmaY=0.1)
        ext = np.repeat(bande, n, axis=0)
        ext *= np.linspace(1, 0.82, n, dtype=np.float32)[:, None, None]
        ext += np.random.default_rng(1).normal(0, 1.0, ext.shape).astype(np.float32)
        img = np.vstack([img, ext])
        H += n

    # 2. produit redimensionné
    prod = Image.open(a.produit).convert('RGBA')
    w = int(round(a.largeur))
    h = int(round(prod.height * w / prod.width))
    prod = np.array(prod.resize((w, h), Image.LANCZOS)).astype(np.float32)
    rgb, alpha = prod[..., :3], prod[..., 3:] / 255

    # 3. accord des couleurs sur la zone de référence
    if a.ref:
        X0, Y0, X1, Y1, rx0, ry0, rx1, ry1 = a.ref
        cible = img[int(Y0):int(Y1), int(X0):int(X1)].reshape(-1, 3).mean(axis=0)
        src = rgb[int(ry0 * h):int(ry1 * h), int(rx0 * w):int(rx1 * w)].reshape(-1, 3).mean(axis=0)
        rgb = rgb * (cible / np.maximum(src, 1))
    rgb *= np.linspace(1.04, 0.84, w, dtype=np.float32)[None, :, None]  # lumière venant de la gauche
    rgb = rgb.clip(0, 255)

    x0, y0 = int(round(a.cx - w / 2)), int(round(a.haut))
    bas = y0 + h

    # 4. ombre de contact sous le pot
    ombre = np.zeros((H, W), np.float32)
    cv2.ellipse(ombre, (int(a.cx + w * 0.04), int(bas - 4)), (int(w * 0.56), 14), 0, 0, 360, 1.0, -1)
    ombre = cv2.GaussianBlur(ombre, (0, 0), 9) * 0.75
    img *= (1 - ombre[..., None])

    # 5. reflet discret sur la surface (produit retourné, qui s'efface vite)
    hr = min(int(h * 0.35), H - bas)
    if hr > 4:
        refl_rgb = rgb[::-1][:hr]
        fondu = np.linspace(0.22, 0, hr, dtype=np.float32)[:, None, None]
        refl_a = alpha[::-1][:hr] * fondu
        zone = img[bas:bas + hr, x0:x0 + w]
        img[bas:bas + hr, x0:x0 + w] = zone * (1 - refl_a) + refl_rgb * refl_a

    # 6. produit
    zone = img[y0:bas, x0:x0 + w]
    img[y0:bas, x0:x0 + w] = zone * (1 - alpha) + rgb * alpha

    Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(a.sortie, quality=95)
    print(a.sortie, img.shape[1], 'x', img.shape[0])


if __name__ == '__main__':
    main()
