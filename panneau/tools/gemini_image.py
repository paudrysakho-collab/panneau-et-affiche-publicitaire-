"""Génère une image avec l'API Gemini (Nano Banana) à partir d'images de référence.

La clé n'est jamais lue ici : le proxy de l'environnement ajoute l'en-tête
x-goog-api-key aux requêtes vers generativelanguage.googleapis.com.

Usage :
    python3 tools/gemini_image.py --prompt fichier.txt --sortie out.png [--modele gemini-3-pro-image] img1.jpg img2.jpg ...
"""
import argparse
import base64
import json
import mimetypes
import sys
from pathlib import Path

import requests

API = 'https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--sortie', required=True)
    ap.add_argument('--modele', default='gemini-3-pro-image')
    ap.add_argument('--format', default='16:9')
    ap.add_argument('--taille', default='4K')
    ap.add_argument('images', nargs='*')
    a = ap.parse_args()

    parts = [{'text': Path(a.prompt).read_text(encoding='utf-8')}]
    for img in a.images:
        mime = mimetypes.guess_type(img)[0] or 'image/jpeg'
        parts.append({'text': f'Image : {Path(img).stem}'})
        parts.append({'inline_data': {'mime_type': mime, 'data': base64.b64encode(Path(img).read_bytes()).decode()}})

    corps = {
        'contents': [{'role': 'user', 'parts': parts}],
        'generationConfig': {
            'responseModalities': ['TEXT', 'IMAGE'],
            'imageConfig': {'aspectRatio': a.format, 'imageSize': a.taille},
        },
    }
    r = requests.post(API.format(a.modele), json=corps, timeout=600)
    d = r.json()
    if 'error' in d:
        print(json.dumps(d['error'], ensure_ascii=False)[:800])
        sys.exit(1)

    n = 0
    for cand in d.get('candidates', []):
        for p in cand.get('content', {}).get('parts', []):
            if 'inlineData' in p:
                sortie = Path(a.sortie)
                if n:
                    sortie = sortie.with_name(f'{sortie.stem}_{n}{sortie.suffix}')
                sortie.write_bytes(base64.b64decode(p['inlineData']['data']))
                print('image :', sortie)
                n += 1
            elif p.get('text'):
                print('texte :', p['text'][:400])
    if not n:
        print('aucune image', json.dumps(d, ensure_ascii=False)[:800])
        sys.exit(1)


if __name__ == '__main__':
    main()
