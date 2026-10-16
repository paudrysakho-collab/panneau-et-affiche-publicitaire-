"""Ramène une image agrandie (Real-ESRGAN x4) à la largeur voulue, en JPEG de qualité impression.

Usage (depuis panneau/) : python3 tools/reduit_hd.py entree.png sortie.jpg LARGEUR
"""
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
entree, sortie, largeur = sys.argv[1], sys.argv[2], int(sys.argv[3])
im = Image.open(entree).convert('RGB')
h = round(im.height * largeur / im.width)
im.resize((largeur, h), Image.LANCZOS).save(sortie, quality=93, subsampling=0)
print(sortie, largeur, 'x', h)
