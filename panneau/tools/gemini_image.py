"""Génère une image avec l'API Gemini (Nano Banana) à partir d'images de référence, avec un garde-fou de dépense.

La clé n'est jamais lue ici : le proxy de l'environnement ajoute l'en-tête
x-goog-api-key aux requêtes vers generativelanguage.googleapis.com.

Garde-fou : chaque appel est inscrit dans un journal CSV (--journal). Avant l'appel, son coût maximal estimé
est réservé ; s'il ferait dépasser --plafond (en dollars, total du journal), l'appel est refusé. Après l'appel,
le coût réel est calculé à partir des tokens facturés renvoyés par Google (usageMetadata) et remplace la
réservation. Les appels lancés en parallèle se partagent le journal sous verrou.

Usage :
    python3 tools/gemini_image.py --prompt fichier.txt --sortie out.png [--modele gemini-3-pro-image]
        [--format 16:9] [--taille 2K] [--numeros] [--journal depenses.csv] [--plafond 4] img1.jpg img2.jpg ...
"""
import argparse
import base64
import csv
import fcntl
import json
import mimetypes
import sys
import time
import uuid
from pathlib import Path

import requests

API = 'https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent'

# Prix en dollars par million de tokens (page officielle des tarifs Gemini API, octobre 2026).
# 'txt' : sortie texte / réflexion. Quand Google ne le publie pas, on compte au prix image (prudent).
PRIX = {
    'gemini-3-pro-image': {'in': 2.00, 'img': 120.0, 'txt': 12.0},
    'gemini-nano-banana-2.1': {'in': 1.50, 'img': 30.0, 'txt': 30.0},
    'gemini-3.1-flash-image': {'in': 0.50, 'img': 60.0, 'txt': 60.0},
}
# Tokens d'une image produite, par taille (mêmes sources)
TOKENS_IMAGE = {
    'gemini-3-pro-image': {'1K': 1120, '2K': 1120, '4K': 2000},
    'gemini-nano-banana-2.1': {'1K': 1120, '2K': 1680, '4K': 3780},
    'gemini-3.1-flash-image': {'1K': 1120, '2K': 1680, '4K': 2520},
}
COLONNES = ['id', 'date', 'modele', 'taille', 'sortie', 'statut', 'tokens_entree', 'tokens_image',
            'tokens_texte', 'cout_usd']


def journal_lire(chemin):
    if not chemin.exists():
        return []
    with open(chemin, newline='') as f:
        return list(csv.DictReader(f))


def depense(lignes):
    """Total engagé : coûts facturés + réservations encore en cours."""
    finies = {l['id'] for l in lignes if l['statut'] in ('facture', 'annule')}
    total = sum(float(l['cout_usd']) for l in lignes if l['statut'] == 'facture')
    total += sum(float(l['cout_usd']) for l in lignes if l['statut'] == 'reserve' and l['id'] not in finies)
    return total


def journal_ecrire(chemin, ligne):
    neuf = not chemin.exists()
    with open(chemin, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLONNES)
        if neuf:
            w.writeheader()
        w.writerow(ligne)


def sous_verrou(chemin, action):
    with open(str(chemin) + '.verrou', 'w') as v:
        fcntl.flock(v, fcntl.LOCK_EX)
        try:
            return action()
        finally:
            fcntl.flock(v, fcntl.LOCK_UN)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prompt', required=True)
    ap.add_argument('--sortie', required=True)
    ap.add_argument('--modele', default='gemini-3-pro-image')
    ap.add_argument('--format', default='16:9')
    ap.add_argument('--taille', default='2K')
    ap.add_argument('--numeros', action='store_true', help='nommer les images « Image 1 », « Image 2 »… (ordre du prompt)')
    ap.add_argument('--journal', default='depenses.csv')
    ap.add_argument('--plafond', type=float, default=4.0, help='dépense totale maximale du journal, en dollars')
    ap.add_argument('--resolution-ref', default='', help="mediaResolution (refusé par les modèles d'image Nano Banana)")
    ap.add_argument('images', nargs='*')
    a = ap.parse_args()
    if a.modele not in PRIX:
        sys.exit(f'modèle sans tarif connu : {a.modele}')
    prix, journal = PRIX[a.modele], Path(a.journal)

    texte = Path(a.prompt).read_text(encoding='utf-8')
    parts = [{'text': texte}]
    for i, img in enumerate(a.images):
        mime = mimetypes.guess_type(img)[0] or 'image/jpeg'
        parts.append({'text': f'Image {i + 1}' if a.numeros else f'Image : {Path(img).stem}'})
        parts.append({'inline_data': {'mime_type': mime, 'data': base64.b64encode(Path(img).read_bytes()).decode()}})

    # coût maximal estimé : entrée large (texte/3 + 1120 tokens par image), image, 4000 tokens de réflexion
    t_img = TOKENS_IMAGE[a.modele].get(a.taille, 4000)
    estime = ((len(texte) / 3 + 1120 * len(a.images)) * prix['in'] + t_img * prix['img'] + 4000 * prix['txt']) / 1e6
    ident = uuid.uuid4().hex[:8]
    base = {'id': ident, 'modele': a.modele, 'taille': a.taille, 'sortie': a.sortie}

    def reserver():
        deja = depense(journal_lire(journal))
        if deja + estime > a.plafond:
            return deja
        journal_ecrire(journal, {**base, 'date': time.strftime('%F %T'), 'statut': 'reserve',
                                 'cout_usd': f'{estime:.4f}'})
        return None
    refus = sous_verrou(journal, reserver)
    if refus is not None:
        sys.exit(f'REFUSÉ : déjà {refus:.2f} $ engagés, cet appel (≈ {estime:.2f} $) dépasserait le plafond de {a.plafond:.2f} $')
    print(f'appel {ident} : {a.modele} {a.taille}, coût maximal estimé {estime:.3f} $')

    config = {'responseModalities': ['TEXT', 'IMAGE'], 'imageConfig': {'aspectRatio': a.format, 'imageSize': a.taille}}
    if a.resolution_ref:
        config['mediaResolution'] = a.resolution_ref
    corps = {'contents': [{'role': 'user', 'parts': parts}], 'generationConfig': config}
    try:
        r = requests.post(API.format(a.modele), json=corps, timeout=900)
    except Exception as e:                       # réseau : on ne sait pas si c'est facturé, la réservation reste
        sys.exit(f'erreur réseau ({e}) : réservation {ident} conservée par prudence')
    try:
        d = r.json()
    except ValueError:
        d = {'error': {'code': r.status_code, 'message': r.text[:600]}}
        if r.status_code < 400:                  # réponse 2xx illisible : facturation possible, on garde la réservation
            sys.exit(f'réponse {r.status_code} illisible : réservation {ident} conservée ; début : {r.text[:300]}')

    if 'error' in d:                             # requête refusée par Google : non facturée
        sous_verrou(journal, lambda: journal_ecrire(journal, {**base, 'date': time.strftime('%F %T'),
                                                              'statut': 'annule', 'cout_usd': '0'}))
        print(json.dumps(d['error'], ensure_ascii=False)[:800])
        sys.exit(1)

    u = d.get('usageMetadata', {})
    t_in = u.get('promptTokenCount', 0)
    details = {x.get('modality'): x.get('tokenCount', 0) for x in u.get('candidatesTokensDetails', [])}
    t_image = details.get('IMAGE', u.get('candidatesTokenCount', 0))
    t_texte = u.get('candidatesTokenCount', 0) - t_image + u.get('thoughtsTokenCount', 0)
    cout = (t_in * prix['in'] + t_image * prix['img'] + t_texte * prix['txt']) / 1e6
    sous_verrou(journal, lambda: journal_ecrire(journal, {
        **base, 'date': time.strftime('%F %T'), 'statut': 'facture', 'tokens_entree': t_in,
        'tokens_image': t_image, 'tokens_texte': t_texte, 'cout_usd': f'{cout:.4f}'}))

    sortie = Path(a.sortie)
    trace = {k: v for k, v in d.items() if k != 'candidates'}
    textes, n = [], 0
    for cand in d.get('candidates', []):
        trace.setdefault('finishReason', cand.get('finishReason'))
        for p in cand.get('content', {}).get('parts', []):
            if 'inlineData' in p and not p.get('thought'):
                f = sortie if not n else sortie.with_name(f'{sortie.stem}_{n}{sortie.suffix}')
                f.write_bytes(base64.b64decode(p['inlineData']['data']))
                print('image :', f)
                n += 1
            elif p.get('text') and not p.get('thought'):
                textes.append(p['text'])
    trace['textes'] = textes
    sortie.with_suffix('.json').write_text(json.dumps(trace, ensure_ascii=False, indent=1))
    total = sous_verrou(journal, lambda: depense(journal_lire(journal)))
    print(f'coût réel {cout:.3f} $ (entrée {t_in}, image {t_image}, texte/réflexion {t_texte} tokens) ; '
          f'total engagé {total:.2f} $ / plafond {a.plafond:.2f} $')
    for t in textes:
        print('texte :', t[:400])
    if not n:
        print('aucune image', json.dumps(trace, ensure_ascii=False)[:800])
        sys.exit(1)


if __name__ == '__main__':
    main()
