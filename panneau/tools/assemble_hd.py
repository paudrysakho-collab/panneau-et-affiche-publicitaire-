"""Assemble la photo HD de l'affiche : Real-ESRGAN partout (verre, capsules, grandes lettres plus nets),
sauf sur les étiquettes à petit texte où l'IA d'agrandissement invente des lettres : là, agrandissement
classique (Lanczos) accentué, fidèle au texte. Raccords fondus.

Usage (depuis panneau/) :
    python3 tools/assemble_hd.py photo_corrigee.jpg esrgan_reduit.jpg sortie.jpg
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None

# zones à petit texte, en pixels de la photo corrigée (1693 x 929)
ETIQUETTES = [
    (38, 498, 220, 719),     # La Favorite
    (229, 574, 346, 756),    # jus de Syrah
    (248, 373, 398, 493),    # Suntory Toki
    (455, 200, 526, 318),    # capsule Tomatin
    (418, 568, 566, 652),    # Tomatin : bandeau bleu LEGACY (ornements, texte) et bande crème
    (559, 349, 678, 557),    # Bastide de Blacailloux
    (671, 502, 851, 694),    # Châteauneuf-du-Pape
    (872, 370, 1031, 566),   # Château de Gragnos
    (1049, 512, 1214, 690),  # Champagne Denis Frézier
    (1116, 174, 1144, 270),  # « CHAMPAGNE » sur la capsule
    (1230, 564, 1347, 709),  # Lutgarde
    (1355, 523, 1469, 706),  # Trompe Souris
    (866, 643, 1077, 789),   # tartinable de courgettes
    (738, 657, 866, 776),    # terrine Silure
    (1496, 676, 1572, 712),  # MAISON GUINGUET
    (1482, 731, 1580, 751),  # plaque CHOCOLAT NOIR
]

src, esr, sortie = sys.argv[1:4]
o = Image.open(src).convert('RGB')
e = Image.open(esr).convert('RGB')
W, H = e.size
k = W / o.width
fidele = o.resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=2.0, percent=70, threshold=2))
m = np.zeros((H, W), np.float32)
for x0, y0, x1, y1 in ETIQUETTES:
    m[int(y0 * k):int(y1 * k), int(x0 * k):int(x1 * k)] = 1
m = cv2.GaussianBlur(m, (0, 0), 4)[..., None]
out = np.array(e).astype(np.float32) * (1 - m) + np.array(fidele).astype(np.float32) * m
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(sortie, quality=93, subsampling=0)
print(sortie, W, 'x', H)
