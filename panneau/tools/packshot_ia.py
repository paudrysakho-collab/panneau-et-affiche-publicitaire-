"""Retouche IA d'UN produit (lumière et matière seulement) via l'API Google AI Studio, SDK google-genai.

La clé n'est jamais lue ici : le proxy de l'environnement ajoute l'en-tête x-goog-api-key.
Chaque appel passe par le journal de dépenses de tools/gemini_image.py (réservation, plafond, coût réel).

Modèles d'image listés par l'API le 17/10/2026 (GET /v1beta/models) et décrits dans la doc officielle
(ai.google.dev/gemini-api/docs/image-generation) : gemini-3-pro-image (Nano Banana Pro, le plus précis),
gemini-nano-banana-2.1, gemini-3.1-flash-image, gemini-3.1-flash-lite-image.
"""
import io
import sys
import time
import uuid
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from gemini_image import PRIX, TOKENS_IMAGE, depense, journal_ecrire, journal_lire, sous_verrou  # noqa: E402

MODELE = 'gemini-3-pro-image'

PROMPT = """Professional packshot retouching of ONE product photo (image 1). Image 2 is a close-up of the same label, for reference only.

This is a LIGHT AND MATERIAL retouch, not a redesign. The output must be the SAME photo, same framing, same size, same position, same silhouette, pixel-aligned with image 1.

STRICTLY FORBIDDEN — any change to text, logos or illustrations:
- Do not rewrite, retype, redraw, sharpen into new shapes, translate or "correct" any letter, number, word, logo, seal, drawing or pattern on the label, the cap, the capsule or the glass.
- Every character must stay exactly as in image 1, at the same place and size. If a text is small or blurry, leave it exactly as it is.
- Do not add any text, logo, watermark or object. Do not remove anything.

ALLOWED — light and material only:
- Studio lighting consistent with a large softbox from the upper left: a clean, long vertical white specular highlight on the left side of the glass, a softer one on the right.
- A thin warm rim light along the left and right contours of the product, separating it from the dark burgundy background.
- Glass: more brilliance and depth, crisp edges, liquid glowing slightly from within ({liquide}).
- Colours: richer and deeper, neutral-warm white balance, deep blacks with detail, no overexposure, no blown highlights on the label.
- Remove small dust, scratches or shop reflections on the glass if any.

Keep the same dark burgundy background, flat and empty. Photorealistic, same aspect ratio."""


def retouche(image, gros_plan, sortie, liquide, journal, plafond, modele=MODELE, taille='2K', format_='9:16'):
    """Envoie le produit (PIL RGB) + gros plan de l'étiquette ; renvoie l'image PIL produite, ou None."""
    from google import genai
    from google.genai import types

    prix, journal = PRIX[modele], Path(journal)
    texte = PROMPT.format(liquide=liquide)
    estime = ((len(texte) / 3 + 1120 * 2) * prix['in'] + TOKENS_IMAGE[modele][taille] * prix['img']
              + 4000 * prix['txt']) / 1e6
    ident = uuid.uuid4().hex[:8]
    base = {'id': ident, 'modele': modele, 'taille': taille, 'sortie': str(sortie)}

    def reserver():
        deja = depense(journal_lire(journal))
        if deja + estime > plafond:
            return deja
        journal_ecrire(journal, {**base, 'date': time.strftime('%F %T'), 'statut': 'reserve', 'cout_usd': f'{estime:.4f}'})
        return None
    refus = sous_verrou(journal, reserver)
    if refus is not None:
        print(f'  REFUSÉ : {refus:.2f} $ engagés, plafond {plafond:.2f} $')
        return None

    def octets(im):
        b = io.BytesIO()
        im.save(b, 'JPEG', quality=95)
        return types.Part.from_bytes(data=b.getvalue(), mime_type='image/jpeg')

    client = genai.Client(api_key='cle-injectee-par-le-proxy')
    try:
        r = client.models.generate_content(
            model=modele,
            contents=[texte, 'Image 1', octets(image), 'Image 2', octets(gros_plan)],
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(aspect_ratio=format_, image_size=taille)))
    except Exception as e:
        # erreur renvoyée par Google (code HTTP) : non facturée ; erreur réseau : réservation gardée par prudence
        if getattr(e, 'code', None):
            sous_verrou(journal, lambda: journal_ecrire(journal, {**base, 'date': time.strftime('%F %T'),
                                                                  'statut': 'annule', 'cout_usd': '0'}))
        print('  erreur API :', str(e)[:300])
        return None

    u = r.usage_metadata
    t_in = u.prompt_token_count or 0
    det = {str(x.modality).split('.')[-1]: x.token_count for x in (u.candidates_tokens_details or [])}
    t_img = det.get('IMAGE', u.candidates_token_count or 0)
    t_txt = (u.candidates_token_count or 0) - t_img + (u.thoughts_token_count or 0)
    cout = (t_in * prix['in'] + t_img * prix['img'] + t_txt * prix['txt']) / 1e6
    sous_verrou(journal, lambda: journal_ecrire(journal, {
        **base, 'date': time.strftime('%F %T'), 'statut': 'facture', 'tokens_entree': t_in,
        'tokens_image': t_img, 'tokens_texte': t_txt, 'cout_usd': f'{cout:.4f}'}))
    total = sous_verrou(journal, lambda: depense(journal_lire(journal)))
    print(f'  appel {modele} {taille} : {cout:.3f} $ (total engagé {total:.2f} $)')
    for c in r.candidates or []:
        for p in (c.content.parts if c.content else []) or []:
            if p.inline_data and not getattr(p, 'thought', False):
                im = Image.open(io.BytesIO(p.inline_data.data)).convert('RGB')
                im.save(sortie)
                return im
    print('  aucune image renvoyée')
    return None
