"""Reconstruit une bande de couleur unie d'une étiquette (bandeau, bande de papier) abîmée par des retouches :
couleur de chaque colonne prise sur des lignes de référence puis lissée (dégradé d'un cylindre), ombrage de chaque ligne pris en médiane
sur la bande elle-même. Le texte est ensuite réécrit par corrige_textes_photo.py.

Usage (depuis panneau/) :
    python3 tools/reconstruit_bande.py entree.jpg sortie.jpg X0 Y0 X1 Y1 RY0 RY1 [clair|sombre]
      X0..Y1  : bande à reconstruire ; RY0..RY1 : lignes de référence pour la couleur par colonne
      clair   : fond plus clair que le texte (papier crème, texte foncé) ; sombre : l'inverse (bandeau bleu)
      uni     : (11e argument) ne pas reprendre l'ombrage ligne par ligne de la bande abîmée
"""
import sys

import cv2
import numpy as np
from PIL import Image

entree, sortie = sys.argv[1], sys.argv[2]
x0, y0, x1, y1, r0, r1 = map(int, sys.argv[3:9])
fond_clair = (sys.argv[9] if len(sys.argv) > 9 else 'clair') == 'clair'
q = 75 if fond_clair else 25          # le texte ne doit pas assombrir (ou éclaircir) le fond estimé
img = np.array(Image.open(entree).convert('RGB')).astype(np.float32)
col = np.percentile(img[r0:r1, x0:x1], q, axis=0)               # couleur par colonne
# ombrage d'un cylindre : variation lente de gauche à droite -> polynôme de degré 2 ajusté en écartant
# les colonnes aberrantes (taches, reflets)
xs = np.arange(x1 - x0, dtype=np.float32)
garde = np.ones(len(xs), bool)
for _ in range(4):
    coefs = [np.polyfit(xs[garde], col[garde, c], 2) for c in range(3)]
    fit = np.stack([np.polyval(k, xs) for k in coefs], axis=1)
    err = np.abs(col - fit).sum(axis=1)
    garde = err < max(6.0, np.percentile(err, 70))
col = fit
L = img[y0:y1, x0:x1] @ np.array([0.299, 0.587, 0.114], np.float32)
ligne = np.percentile(L, q, axis=1)                              # ombrage par ligne, sans le texte
ref = np.percentile(col @ np.array([0.299, 0.587, 0.114], np.float32), q)
ombre = np.convolve(np.pad(ligne / max(ref, 1), 2, mode='edge'), np.ones(5) / 5, 'valid')
if len(sys.argv) > 10 and sys.argv[10] == 'uni':   # bande abîmée sur toute sa hauteur : pas d'ombrage repris
    ombre = np.ones_like(ombre)
neuf = col[None] * ombre[:, None, None]
neuf += np.random.default_rng(5).normal(0, 1.2, neuf.shape).astype(np.float32)
img[y0:y1, x0:x1] = neuf
Image.fromarray(img.clip(0, 255).astype(np.uint8)).save(sortie, quality=95)
print(sortie)
