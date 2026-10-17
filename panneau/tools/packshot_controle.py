"""Contrôle d'une retouche IA d'un produit, comparée à l'original : silhouette, lettres des étiquettes, OCR.

- alignement : l'image IA est recalée sur l'original (ECC affine, dans le masque du produit) ;
- silhouette : masque du produit dans l'image IA (écart au fond envoyé) comparé au masque d'origine (IoU) ;
- lettres : dans chaque zone d'étiquette, la structure fine (passe-haut) est comparée par petites tuiles
  (corrélation) : un relief changé, une lettre redessinée ou un mot différent fait chuter la tuile ;
- OCR (tesseract, fra+eng) : chaque mot lu de façon stable sur l'original (3 lectures sur 4, confiance 85)
  doit se retrouver à l'identique dans l'image retouchée.
Une seule tuile de texte sous le seuil, ou un seul mot manquant : rejet.
"""
import re
import unicodedata

import cv2
import numpy as np
from PIL import Image

SEUIL_TUILE = 0.90      # corrélation minimale d’une tuile de texte : témoin ré-éclairé par code 0,99 ; IA redessinée 0,72–0,84
SEUIL_IOU = 0.975       # recouvrement minimal des silhouettes
TUILE = 40


def gris(a):
    return cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255


def aligne(ref, ia, masque):
    """Recale ia (RGB uint8, même taille que ref) sur ref ; renvoie (ia recalée, score ECC)."""
    g1, g2 = gris(ref), gris(ia)
    w = np.eye(2, 3, dtype=np.float32)
    m = (masque > 0.5).astype(np.uint8)
    try:
        cc, w = cv2.findTransformECC(g1, g2, w, cv2.MOTION_AFFINE,
                                     (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), m, 5)
    except cv2.error:
        cc = 0.0
    h, l = ref.shape[:2]
    out = cv2.warpAffine(ia, w, (l, h), flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE)
    return out, float(cc)


def passe_haut(g):
    return cv2.GaussianBlur(g, (0, 0), 0.8) - cv2.GaussianBlur(g, (0, 0), 3.5)


def tuiles_texte(ref, ia, boite):
    """Corrélation par tuile du passe-haut, sur les tuiles qui contiennent du texte dans l'original."""
    x0, y0, x1, y1 = boite
    a, b = passe_haut(gris(ref))[y0:y1, x0:x1], passe_haut(gris(ia))[y0:y1, x0:x1]
    res = []
    pas = TUILE // 2
    energie = np.sqrt((a ** 2).mean()) + 1e-6
    for y in range(0, a.shape[0] - TUILE + 1, pas):
        for x in range(0, a.shape[1] - TUILE + 1, pas):
            ta, tb = a[y:y + TUILE, x:x + TUILE], b[y:y + TUILE, x:x + TUILE]
            ea = np.sqrt((ta ** 2).mean())
            if ea < 1.2 * energie or ea < 0.012:          # tuile sans texte net
                continue
            ta, tb = ta - ta.mean(), tb - tb.mean()
            n = np.sqrt((ta ** 2).sum() * (tb ** 2).sum()) + 1e-9
            res.append((float((ta * tb).sum() / n), x0 + x, y0 + y))
    return res


def _norm(m):
    return unicodedata.normalize('NFC', m.upper())


def _prepare_ocr(rgb, boite, f):
    """Gris normalisé par la lumière locale (une retouche de lumière ne change pas la lecture), agrandi."""
    x0, y0, x1, y1 = boite
    g = cv2.cvtColor(rgb[y0:y1, x0:x1], cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = cv2.resize(g, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    n = g / (cv2.GaussianBlur(g, (0, 0), 6 * f) + 8)
    n = np.clip((n - n.min()) / (np.percentile(n, 99.5) - n.min() + 1e-6), 0, 1)
    return Image.fromarray((n * 255).astype(np.uint8))


def lectures_ocr(rgb, boite, conf_min):
    """4 lectures tesseract (2 agrandissements x 2 modes de page) ; un ensemble de mots par lecture."""
    import pytesseract
    res = []
    for f in (2.5, 3.5):
        for psm in ('11', '6'):
            d = pytesseract.image_to_data(_prepare_ocr(rgb, boite, f), lang='fra+eng', config='--psm ' + psm,
                                          output_type=pytesseract.Output.DICT)
            s = set()
            for t, cf in zip(d['text'], d['conf']):
                t = re.sub(r"[^\wÀ-ÿ'’-]", '', t)
                if len(t) >= 4 and float(cf) >= conf_min and re.fullmatch(r"[A-Za-zÀ-ÿ'’-]+", t):
                    s.add(_norm(t))
            res.append(s)
    return res


def mots_fiables(rgb, boite):
    """Mots de l'original lus avec confiance dans au moins 3 lectures sur 4."""
    r = lectures_ocr(rgb, boite, 85)
    tous = set().union(*r)
    return sorted(m for m in tous if sum(m in s for s in r) >= 3)


def mots_lus(rgb, boite):
    return set().union(*lectures_ocr(rgb, boite, 0))


def controle(ref, ia, masque, masque_ia, boites):
    """ref, ia : RGB uint8 de même taille (ia déjà recalée). boites : zones d'étiquette en pixels.
    Renvoie (accepté, rapport dict)."""
    inter = ((masque > 0.5) & (masque_ia > 0.5)).sum()
    union = ((masque > 0.5) | (masque_ia > 0.5)).sum()
    iou = inter / max(union, 1)
    pires, manquants, lus = [], [], 0
    for b in boites:
        t = tuiles_texte(ref, ia, b)
        pires += [x for x in t if x[0] < SEUIL_TUILE]
        mr = mots_fiables(ref, b)
        mi = mots_lus(ia, b) if mr else set()
        lus += len(mr)
        manquants += [m for m in mr if m not in mi]
    ok = iou >= SEUIL_IOU and not pires and not manquants
    rapport = {'iou': round(float(iou), 4), 'tuiles_rejetees': len(pires),
               'pire_tuile': round(min([p[0] for p in pires], default=1.0), 3),
               'mots_ocr_lus': lus, 'mots_manquants': manquants, 'accepte': ok,
               'positions_tuiles': [(p[1], p[2]) for p in sorted(pires)[:12]]}
    return ok, rapport
