"""Prépare le pack d'images de référence (une image par produit, dans l'ordre de gauche à droite de
l'affiche) pour une génération par IA (ChatGPT, Gemini), plus la composition actuelle comme modèle.

Aucune retouche ne touche aux étiquettes : recadrage, fond, agrandissement Lanczos seulement.
  - Syrah, Silure et chocolat viennent de la photo de groupe (style-reference) : les produits voisins
    sont retirés. Sur la Syrah, le pot Silure cachait le bord droit (marge unie de l'étiquette et
    verre) : ce bord est refait en miroir du bord gauche, identique.
  - Tomatin : la bouteille seule, sans son étui.

Usage (depuis panneau/) :
    python3 tools/pack_references.py bouteilles-gemini/pack-derniere-tentative
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None
B = Path('bouteilles-gemini')
N = B / 'nouveaux-produits'
REF = B / 'style-reference-terrines-chocolat.jpg'
COTE = 1800          # plus grand côté visé pour les images de produits


def agrandi(im):
    k = COTE / max(im.size)
    if k <= 1.05:
        return im
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    return im.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=2))


def marge(im, m=0.06, fond=(255, 255, 255)):
    """Ajoute une marge blanche autour (le produit ne touche pas le bord)."""
    dx, dy = round(im.width * m), round(im.height * m * 0.5)
    o = Image.new('RGB', (im.width + 2 * dx, im.height + 2 * dy), fond)
    o.paste(im, (dx, dy))
    return o


def syrah():
    """Syrah de la photo de groupe. Le pot Silure cache son bord droit (y 556-1000, x > 576) :
    marge unie de l'étiquette prolongée depuis la colonne 574, bord de verre recopié de la partie
    visible juste au-dessus du pot (même bouteille, même reflet), coin du talon en miroir du gauche
    (la bouteille est symétrique : bas à y 946 en x 574 comme en x 370), sol fondu vers le fond."""
    import cv2
    a = np.array(Image.open(REF).convert('RGB')).astype(np.float32)
    y0, y1, xg, xv, xd = 556, 1030, 576, 605, 664
    xs = np.arange(xg, xd)
    L = a.mean(axis=2)
    # 1. verre : marge de l'étiquette et verre prolongés (colonne 574), bord droit recopié au-dessus du pot,
    #    coin arrondi du talon en miroir du coin gauche
    verre = a.copy()
    verre[y0:y1, xg:xv] = a[y0:y1, 574:575]
    profil = a[530:552, xv:xd].mean(axis=0)
    bruit = np.random.default_rng(7).normal(0, 1.2, (y1 - y0, xd - xv, 3)).astype(np.float32)
    verre[y0:y1, xv:xd] = profil[None] + bruit
    yt = 900
    miroir = a[yt:y1][:, 944 - xs]
    tx = np.clip((xs - 598) / 14, 0, 1)[None, :, None]
    ty = np.clip(np.arange(y1 - yt) / 12, 0, 1)[:, None, None]
    verre[yt:y1, xg:xd] = verre[yt:y1, xg:xd] * (1 - tx * ty) + miroir * (tx * ty)
    # 2. silhouette de la bouteille dans la zone cachée : bas et coin du côté gauche, en miroir
    forme = np.zeros(a.shape[:2], np.float32)
    for x in xs:
        xm = 944 - x
        col = np.where(L[880:1040, xm] < 150)[0]
        bas = 880 + col.max() if len(col) else 0
        if xm >= 312:
            forme[y0:bas + 1, x] = 1
    forme = cv2.GaussianBlur(forme, (0, 0), 0.8)[..., None]
    # 3. hors bouteille : fond / sol en miroir du côté gauche, raccordé au sol réel (x 575) sur 30 px
    u = np.clip((xs - 575) / 30, 0, 1)[None, :, None]
    dehors = a[y0:y1, 575:576] * (1 - u) + a[y0:y1][:, 944 - xs] * u
    neuf = a.copy()
    neuf[y0:y1, xg:xd] = verre[y0:y1, xg:xd] * forme[y0:y1, xg:xd] + dehors * (1 - forme[y0:y1, xg:xd])
    m = np.zeros(a.shape[:2], np.float32)
    m[y0:y1, xg:xd] = 1
    m[y0:y0 + 8, xg:xd] *= np.linspace(0, 1, 8)[:, None]             # fondu en haut
    m[y0:y1, xg:xg + 2] *= np.array([0.5, 1.0])[None, :]             # fondu à gauche
    a = a * (1 - m[..., None]) + neuf * m[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).crop((280, 20, 664, 1030))


def silure():
    """Pot Silure détouré (BiRefNet), limité à ses propres bords : le pot « Poissons de Loire » collé
    derrière à droite et la Syrah à gauche sont retirés, fond blanc de la photo."""
    import os
    import cv2
    x0, y0 = 540, 520
    im = Image.open(REF).convert('RGB').crop((x0, y0, 1030, 1070))
    cache = os.environ.get('CACHE_SILURE')
    if cache and os.path.exists(cache):
        al = np.load(cache).astype(np.float32) / 255
    else:
        from rembg import new_session, remove
        al = np.array(remove(im, session=new_session('birefnet-general')))[..., 3].astype(np.float32) / 255
    # bords du pot Silure relevés sur la photo (couvercle jusqu'à x 995, corps jusqu'à x 983)
    poly = np.array([(0, 0), (395, 0), (395, 46), (412, 52), (440, 64), (456, 76), (456, 113), (446, 119), (443, 130),
                     (444, 445), (436, 472), (416, 500), (0, 520)], np.int32)
    lim = np.zeros(al.shape, np.uint8)
    cv2.fillPoly(lim, [poly], 1)
    lim = cv2.GaussianBlur(lim.astype(np.float32), (0, 0), 0.7)
    al = (al * lim)[..., None]
    fond = np.array([246, 246, 245], np.float32)
    out = np.array(im).astype(np.float32) * al + fond * (1 - al)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8)).crop((25, 20, 480, 530))


def tomatin():
    """Bouteille Tomatin seule : le bord droit, devant l'étui, est retrouvé par symétrie du bord gauche
    (axe du col, x = 231) ; tout ce qui est à droite devient blanc."""
    im = Image.open(N / 'whisky_Tomatin_Legacy_officiel.jpg').convert('RGB').crop((0, 0, 420, 876))
    a = np.array(im).astype(np.float32)
    L = a.mean(axis=2)
    xs = np.arange(a.shape[1])
    gauche = np.array([(np.where(L[y, :230] < 235)[0].min() if (L[y, :230] < 235).any() else 231)
                       for y in range(a.shape[0])], np.float32)
    # bord gauche lissé (reflets du verre gravé) : médiane puis moyenne glissantes
    from scipy.ndimage import median_filter, uniform_filter1d
    gauche = uniform_filter1d(median_filter(gauche, 9, mode='nearest'), 5, mode='nearest')
    for y in range(a.shape[0]):
        d = 462 - gauche[y]                                  # bord droit = symétrique du gauche
        t = np.clip((xs - d) / 2.0, 0, 1)[:, None]          # 2 px de fondu
        a[y] = a[y] * (1 - t) + 255 * t
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).crop((40, 0, 420, 876))


def tomatin_magasin():
    """La vraie bouteille Tomatin du magasin (haut de l'étiquette imprimé sur le verre, panneau bleu à partir de
    LEGACY), détourée (BiRefNet). L'étui bleu derrière, à droite, est retiré : bord droit relevé à la main sur la
    photo (la bouteille penche un peu, pas de symétrie simple) ; au niveau du col, symétrie du bord gauche."""
    import os
    import cv2
    im = Image.open(N / 'whisky_Tomatin_Legacy_photo.jpg').convert('RGB')
    cache = os.environ.get('CACHE_TOMATIN')
    if cache and os.path.exists(cache):
        al = np.load(cache).astype(np.float32) / 255
    else:
        from rembg import new_session, remove
        al = np.array(remove(im, session=new_session('birefnet-general')))[..., 3].astype(np.float32) / 255
    H, W = al.shape
    bord_d = np.interp(np.arange(H), [400, 550, 600, 700, 750], [324, 312, 308, 300, 296])
    x = np.arange(W)
    for y in range(H):
        if y < 400:
            # col et épaules : segment qui contient l'axe, bord droit = symétrique du gauche (axe x ≈ 166,5)
            if al[y, 166] <= 0.5:
                continue
            g = 166
            while g > 0 and al[y, g - 1] > 0.5:
                g -= 1
            al[y, :g] = 0                      # trait vertical isolé du décor à gauche
            d = 2 * (166.5 + max(0, y - 330) * 0.02) - g
        elif y <= 750:
            d = bord_d[y]                      # bord droit relevé à la main (étui bleu derrière)
        else:
            continue
        al[y] *= np.clip(d + 1 - x, 0, 1)
    # étui bleu vu à travers / derrière le bord droit du verre (x > 292, à droite de l'étiquette) :
    # remplacé par le verre doré de la même ligne, assombri vers le bord
    a = np.array(im).astype(np.float32)
    for y in range(330, 760):
        x0 = 292
        ref = a[y, x0 - 6:x0].mean(axis=0)
        for x in range(x0, W):
            r, g_, b = a[y, x]
            if b > r + 15 or (b > 90 and b > g_):
                t = min(1.0, (x - x0) / 30)
                a[y, x] = ref * (1 - 0.35 * t)
    al = cv2.GaussianBlur(al, (0, 0), 0.6)[..., None]
    out = a * al + 255 * (1 - al)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))


def main():
    sortie = Path(sys.argv[1])
    sortie.mkdir(parents=True, exist_ok=True)
    produits = [
        ('01_rhum_La_Favorite_Coeur_de_Canne', Image.open(B / '8_rhum_La_Favorite_Coeur_de_Canne.jpg')),
        ('02_jus_de_raisin_Syrah', syrah()),
        ('03_whisky_Suntory_Toki', Image.open(B / '1_whisky_Suntory_Toki.jpg')),
        ('04_whisky_Tomatin_Legacy', tomatin_magasin()),
        ('05_rose_Bastide_de_Blacailloux_JOIO', Image.open(B / '2_rose_Bastide_de_Blacailloux.jpg')),
        ('06_rouge_Chateauneuf-du-Pape_Prieure_des_Papes', Image.open(B / '4_rouge_Chateauneuf-du-Pape_Prieure_des_Papes.jpg')),
        ('07_rouge_Chateau_de_Gragnos_Lou_Daro', Image.open(B / '3_rouge_Chateau_de_Gragnos_Lou_Daro.jpg')),
        ('08_champagne_Denis_Frezier_Cuvee_des_Trois_Crus', Image.open(B / '6_champagne_Denis_Frezier_Trois_Crus.jpg')),
        ('09_biere_Lutgarde_Blonde', Image.open(N / 'biere_Lutgarde_Blonde_photo.jpg')),
        ('10_biere_Trompe_Souris_Blonde', Image.open(N / 'biere_Trompe_Souris_Blonde_photo.jpg')),
        ('11_chocolats_Maison_Guinguet', Image.open(REF).crop((1345, 0, 1830, 1080))),
        ('12_terrine_Gouts_de_Loire_Silure', silure()),
        ('13_tartinable_courgettes_Atelier_d_Emile', Image.open(N / 'tartinable_courgettes_officiel.jpg')),
    ]
    for nom, im in produits:
        im = agrandi(im.convert('RGB'))
        im.save(sortie / f'{nom}.jpg', quality=95)
        print(nom, im.size)
    comp = Image.open('public/produits/vitrine_sombre.jpg').convert('RGB')
    comp = comp.resize((2400, round(2400 * comp.height / comp.width)), Image.LANCZOS)
    comp.save(sortie / '14_composition_actuelle_modele.jpg', quality=93)
    print('14_composition_actuelle_modele', comp.size)


if __name__ == '__main__' and '--planche' not in sys.argv:
    main()


def planche(dossier):
    """Planche unique des 13 produits, numérotés (pour les outils limités à 10 images, ex. Gemini)."""
    from PIL import ImageDraw, ImageFont
    fs = sorted(Path(dossier).glob('[01][0-9]_*.jpg'))[:13]
    cw, ch, marge = 600, 1000, 40
    W, H = 7 * cw + 2 * marge, 2 * ch + 3 * marge
    o = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(o)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 34)
    except OSError:
        f = ImageFont.load_default()
    for i, p in enumerate(fs):
        r, c = (0, i) if i < 7 else (1, i - 7 + 0.5)
        x0, y0 = marge + c * cw, marge + r * (ch + marge)
        im = Image.open(p).convert('RGB')
        k = min((cw - 30) / im.width, (ch - 70) / im.height)
        im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        o.paste(im, (round(x0 + (cw - im.width) / 2), round(y0 + 60 + (ch - 70 - im.height))))
        cx = x0 + cw / 2                                  # numéro centré au-dessus du produit
        d.ellipse((cx - 26, y0, cx + 26, y0 + 52), fill=(60, 60, 60))
        n = str(i + 1)
        tw = d.textlength(n, font=f)
        d.text((cx - tw / 2, y0 + 7), n, fill=(255, 255, 255), font=f)
    o.save(Path(dossier) / '15_planche_13_produits.jpg', quality=93)
    print('15_planche_13_produits', o.size)


if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[2] == '--planche':
    planche(sys.argv[1])
