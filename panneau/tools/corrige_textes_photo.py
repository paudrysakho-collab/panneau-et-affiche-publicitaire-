"""Corrige les textes inventés par l'IA sur les étiquettes de la photo studio (version sombre).

Pour chaque ligne fautive : on repère les pixels du texte dans la zone (plus sombres ou plus clairs
que le papier, ligne par ligne), on les efface par inpainting, puis on réécrit le vrai texte
(même hauteur de capitales, couleur reprise du texte d'origine), éventuellement limité à une zone
visible quand une autre bouteille passe devant.

Usage (depuis panneau/), le dernier argument choisit la liste de corrections (v8 par défaut) :
    python3 tools/corrige_textes_photo.py bouteilles-gemini/resultat_gemini_v8_sombre.jpg public/produits/vitrine_sombre.jpg v8
    python3 tools/corrige_textes_photo.py bouteilles-gemini/resultat_gemini_v10_11produits.jpg public/produits/vitrine_sombre.jpg v10
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RACINE = Path(__file__).resolve().parent.parent
POLICES = {
    'sans': RACINE / 'public/fonts/Montserrat.ttf',
    'serif': RACINE / 'public/fonts/CormorantGaramond.ttf',
    'serif-it': RACINE / 'public/fonts/CormorantGaramond-Italic.ttf',
}
SUR = 8  # suréchantillonnage du rendu du texte

# zone = (x0, y0, x1, y1) contenant l'ancien texte ; mode = 'sombre' (texte plus foncé que le fond) ou 'clair'
# x, y = point d'ancrage (centre des capitales) ; align = 'c' (centré sur x) ou 'g' (commence à x) ou 'd' (finit à x)
# cap = hauteur des capitales en px ; visible = zone où l'on a le droit de dessiner (bouteille devant)
CORRECTIONS_V8 = [
    # Jus de raisin Syrah
    dict(zone=(116, 870, 224, 886), mode='sombre', texte='PUR JUS DE RAISINS', police='sans', poids='SemiBold', x=169, y=878, cap=8.0, align='c'),
    dict(zone=(130, 888, 208, 899), mode='sombre', texte='SANS SUCRE AJOUTÉ*', police='sans', poids='Medium', x=169, y=893.5, cap=4.6, align='c'),
    # Whisky Toki (le jus passe devant à gauche)
    dict(zone=(248, 703, 330, 757), mode='sombre', texte=None, cap=5),
    dict(texte='FROM THE HOUSE OF', police='sans', poids='SemiBold', x=236, y=710, cap=4.3, align='g', couleur=(45, 38, 36), visible=(248, 700, 400, 760)),
    dict(texte='SUNTORY WHISKY', police='sans', poids='SemiBold', x=236, y=719.5, cap=4.3, align='g', couleur=(45, 38, 36), visible=(248, 700, 400, 760)),
    dict(texte='ESTABLISHED 1923', police='sans', poids='SemiBold', x=236, y=729, cap=4.3, align='g', couleur=(45, 38, 36), visible=(248, 700, 400, 760)),
    dict(texte='JAPANESE WHISKY', police='serif', poids='Medium', x=236, y=740, cap=4.6, align='g', couleur=(88, 78, 72), visible=(248, 700, 400, 760)),
    dict(texte='43% ALC./VOL. · 70 cl', police='serif', poids='Medium', x=236, y=750, cap=4.3, align='g', couleur=(88, 78, 72), visible=(248, 700, 400, 760)),
    # Bastide de Blacailloux
    dict(zone=(468, 780, 556, 794), mode='sombre', texte='VIN DE PROVENCE', police='sans', poids='SemiBold', x=511, y=787, cap=6.6, align='c'),
    dict(zone=(440, 800, 580, 834), mode='sombre', texte=None, cap=5),
    dict(texte='Famille Chamson Vignerons depuis 1917', police='serif-it', poids='SemiBold', x=510, y=807, cap=4.4, align='c', couleur=(70, 50, 48)),
    dict(texte='COTEAUX VAROIS EN PROVENCE', police='sans', poids='Medium', x=510, y=816.5, cap=4.6, align='c', couleur=(70, 50, 48)),
    dict(texte="APPELLATION D'ORIGINE PROTÉGÉE", police='sans', poids='Regular', x=510, y=825.3, cap=3.2, align='c', couleur=(90, 70, 66)),
    # Château de Gragnos
    dict(zone=(638, 738, 702, 750), mode='sombre', texte='DEPUIS 1710', police='sans', poids='Medium', x=670, y=744.5, cap=4.6, align='c'),
    # Châteauneuf-du-Pape (le pot de terrine passe devant à droite)
    dict(zone=(745, 925, 838, 936), mode='sombre', texte="APPELLATION D'ORIGINE PROTÉGÉE", police='serif', poids='SemiBold', x=748, y=930.5, cap=5.0, align='g', visible=(740, 920, 838, 940)),
    # Château Balac
    dict(zone=(1090, 795, 1166, 811), mode='sombre', texte='SUPÉRIEUR', police='serif', poids='Medium', x=1092, y=803.5, cap=8.6, align='g'),
    dict(zone=(1014, 818, 1130, 832), mode='sombre', texte='FAMILLE TOUCHAIS', police='serif', poids='SemiBold', x=1072, y=825.5, cap=6.4, align='c'),
    # Champagne Denis Frézier (le pot de terrine passe devant à gauche)
    dict(zone=(1222, 813, 1392, 823), mode='sombre', texte='PRODUCED IN THE HEART OF CHAMPAGNE', police='sans', poids='Medium', x=1306, y=818.2, cap=4.6, align='c'),
    dict(zone=(1276, 848, 1394, 882), mode='sombre', texte='Cuvée des Trois Crus', police='serif-it', poids='Medium', x=1388, y=862, cap=10.0, align='d', visible=(1276, 845, 1400, 880)),
    dict(zone=(1268, 912, 1352, 924), mode='sombre', texte='ESTATE BOTTLED', police='sans', poids='Medium', x=1310, y=918, cap=5.6, align='c', visible=(1275, 905, 1400, 930)),
    # Divin (La Favorite passe devant à droite)
    dict(zone=(1434, 843, 1534, 855), mode='sombre', texte='Sans alcool - Alcohol free', police='sans', poids='Medium', italique=True, x=1437, y=849, cap=4.4, align='g', visible=(1430, 840, 1534, 858)),
    # Rhum La Favorite (le sachet passe devant à droite)
    dict(zone=(1606, 769, 1668, 778), mode='sombre', texte='FONDÉE EN 1842', police='sans', poids='SemiBold', x=1637, y=773.5, cap=3.4, align='c'),
    dict(zone=(1592, 845, 1712, 859), mode='sombre', texte='RHUM AGRICOLE AMBRÉ', police='sans', poids='SemiBold', x=1652, y=852, cap=6.4, align='c', visible=(1585, 840, 1712, 862)),
    dict(zone=(1580, 900, 1722, 935), mode='clair', texte=None),
    dict(texte="APPELLATION D'ORIGINE CONTRÔLÉE", police='sans', poids='Medium', x=1648, y=906.5, cap=3.6, align='c', couleur=(214, 200, 175), visible=(1580, 900, 1712, 935)),
    dict(texte='RÉCOLTÉ, DISTILLÉ ET MIS EN BOUTEILLE', police='sans', poids='Medium', x=1648, y=917.5, cap=3.2, align='c', couleur=(214, 200, 175), visible=(1580, 900, 1712, 935)),
    dict(texte='À LA DISTILLERIE LA FAVORITE PAR LA FAMILLE DORMOY', police='sans', poids='Medium', x=1648, y=925, cap=3.2, align='c', couleur=(214, 200, 175), visible=(1580, 900, 1712, 935)),
    # Terrines Goûts de Loire
    dict(zone=(934, 1036, 966, 1052), mode='sombre', texte='BIO', police='sans', poids='Bold', x=949, y=1044, cap=7.2, align='c', couleur=(40, 12, 16)),
    dict(zone=(1158, 1019, 1192, 1033), mode='sombre', texte='BIO', police='sans', poids='Bold', x=1175, y=1026, cap=7.2, align='c'),
    dict(zone=(1070, 999, 1272, 1017), mode='sombre', ecart=7, texte='Touraine Sauvignon et aromates', police='serif-it', poids='Bold', x=1176, y=1005, cap=7.6, align='c', couleur=(12, 16, 30), gras=2.6, visible=(1068, 997, 1270, 1018)),
]

# « à la Tomate séchée » : écriture manuscrite reprise de la photo de référence (où elle est juste).
TOMATE_V8 = dict(source=(645, 884, 950, 928), cible=(868, 1005, 1034, 1038), zone=(866, 1006, 1036, 1038))

# Photo à 11 produits (resultat_gemini_v10_11produits.jpg)
CREME_LUT = (238, 224, 196)
CORRECTIONS_V10 = [
    # Rhum La Favorite
    dict(zone=(134, 801, 192, 811), mode='sombre', texte='FONDÉE EN 1842', police='sans', poids='SemiBold', x=163, y=806, cap=3.4, align='c'),
    dict(zone=(120, 862, 242, 880), mode='sombre', plein=True, texte='Cœur de Canne', police='serif', poids='Bold', x=181, y=871.5, cap=8.6, align='c', couleur=(150, 100, 30), gras=2.2),
    dict(zone=(120, 880, 242, 893), mode='sombre', texte='RHUM AGRICOLE AMBRÉ', police='sans', poids='SemiBold', x=181, y=886.5, cap=5.8, align='c'),
    dict(zone=(172, 919, 194, 932), mode='clair', plein=True, texte='ans', police='serif', poids='Bold', x=183, y=922, cap=4.2, align='c', couleur=(250, 240, 230)),
    dict(zone=(112, 952, 272, 984), mode='clair', texte=None),
    dict(texte="APPELLATION D'ORIGINE CONTRÔLÉE", police='sans', poids='Medium', x=190, y=957.5, cap=3.4, align='c', couleur=(214, 200, 175), visible=(122, 950, 262, 984)),
    dict(texte='RÉCOLTÉ, DISTILLÉ ET MIS EN BOUTEILLE', police='sans', poids='Medium', x=192, y=967, cap=3.0, align='c', couleur=(214, 200, 175), visible=(122, 950, 262, 984)),
    dict(texte='À LA DISTILLERIE LA FAVORITE PAR LA FAMILLE DORMOY', police='sans', poids='Medium', x=192, y=975.5, cap=3.0, align='c', couleur=(214, 200, 175), visible=(122, 950, 262, 984)),
    # Jus de raisin Syrah
    dict(zone=(352, 805, 396, 817), mode='sombre', texte='CÉPAGE', police='sans', poids='SemiBold', x=374, y=811, cap=5.6, align='c'),
    dict(zone=(326, 869, 422, 881), mode='sombre', texte='SANS SUCRE AJOUTÉ*', police='sans', poids='Medium', x=374, y=875, cap=3.8, align='c'),
    # Whisky Toki (le jus passe devant à gauche)
    dict(zone=(440, 690, 540, 745), mode='sombre', texte=None, cap=5),
    dict(texte='FROM THE HOUSE OF', police='sans', poids='SemiBold', x=436, y=696, cap=4.4, align='g', couleur=(45, 38, 36), visible=(440, 686, 560, 748)),
    dict(texte='SUNTORY WHISKY', police='sans', poids='SemiBold', x=436, y=706, cap=4.4, align='g', couleur=(45, 38, 36), visible=(440, 686, 560, 748)),
    dict(texte='ESTABLISHED 1923', police='sans', poids='SemiBold', x=436, y=716, cap=4.4, align='g', couleur=(45, 38, 36), visible=(440, 686, 560, 748)),
    dict(texte='JAPANESE WHISKY', police='serif', poids='Medium', x=436, y=729, cap=4.4, align='g', couleur=(88, 78, 72), visible=(440, 686, 560, 748)),
    dict(texte='43% ALC./VOL. · 70 cl', police='serif', poids='Medium', x=436, y=739, cap=4.2, align='g', couleur=(88, 78, 72), visible=(440, 686, 560, 748)),
    # Bastide de Blacailloux (le Toki passe devant à gauche, le Gragnos à droite)
    dict(zone=(640, 754, 696, 766), mode='sombre', plein=True, texte='ROSÉ', police='sans', poids='Medium', x=660, y=760, cap=4.4, align='c'),
    dict(zone=(634, 765, 716, 779), mode='sombre', texte='VIN DE PROVENCE', police='sans', poids='SemiBold', x=674, y=771.7, cap=5.2, align='c', visible=(622, 760, 724, 782)),
    dict(zone=(622, 787, 724, 816), mode='sombre', texte=None, cap=4),
    dict(texte='COTEAUX VAROIS EN PROVENCE', police='sans', poids='Medium', x=674, y=793, cap=3.6, align='c', couleur=(70, 50, 48), visible=(622, 784, 724, 818)),
    dict(texte="APPELLATION D'ORIGINE PROTÉGÉE", police='sans', poids='Regular', x=674, y=802, cap=3.0, align='c', couleur=(90, 70, 66), visible=(622, 784, 724, 818)),
    # Château de Gragnos
    dict(zone=(804, 781, 884, 793), mode='sombre', texte='DEPUIS 1710', police='sans', poids='Medium', x=844, y=787, cap=4.4, align='c'),
    # Châteauneuf-du-Pape : « LE PRIEURÉ » (le pot de courgettes passe devant en bas)
    dict(zone=(1088, 811, 1186, 827), mode='sombre', texte='LE PRIEURÉ', police='serif', poids='SemiBold', x=1136, y=821, cap=9.4, align='c', visible=(1080, 806, 1200, 827)),
    # Champagne Denis Frézier (le pot de courgettes passe devant à gauche)
    dict(zone=(1244, 813, 1414, 825), mode='sombre', texte='PRODUCED IN THE HEART OF CHAMPAGNE', police='sans', poids='Medium', x=1330, y=819, cap=4.2, align='c'),
    dict(zone=(1288, 853, 1420, 882), mode='sombre', texte='Cuvée des Trois Crus', police='serif-it', poids='Medium', x=1416, y=867, cap=10.0, align='d', visible=(1290, 848, 1424, 884)),
    dict(zone=(1280, 887, 1382, 901), mode='sombre', texte='PREMIER BRUT', police='sans', poids='Medium', x=1332, y=894, cap=6.6, align='c', visible=(1288, 884, 1400, 904)),
    dict(zone=(1280, 914, 1376, 926), mode='sombre', texte='ESTATE BOTTLED', police='sans', poids='Medium', x=1330, y=920, cap=4.8, align='c', visible=(1288, 910, 1400, 928)),
    # Bière Lutgarde : textes courbes sur la bande rouge + « 33 cl / Alc vol 6% »
    dict(anneau=(1502, 859.5, 75, 91.5, 83.5, 111.5, 740, 840), mode='clair', texte=None, cap=6),
    dict(anneau=(1502, 859.5, 75, 91.5, 83.5, 111.5, 890, 975), mode='clair', texte=None, cap=6),
    dict(texte='BELGIAN ABBEY BEER', police='sans', poids='Bold', arc=(1502, 859.5, 79, 101, -157, -23), cap=5.6, couleur=CREME_LUT),
    dict(texte="Abbaye d'Aywiers", police='serif', poids='Bold', arc=(1502, 859.5, 79, 101, 142, 38), cap=6.4, couleur=CREME_LUT),
    dict(zone=(1474, 912, 1530, 938), mode='sombre', texte=None, cap=5),
    dict(texte='33 cl', police='serif', poids='Bold', x=1502, y=919.5, cap=5.4, align='c', couleur=(70, 30, 30)),
    dict(texte='Alc vol 6%', police='serif', poids='Bold', x=1502, y=930, cap=4.4, align='c', couleur=(70, 30, 30)),
    # Terrine Silure de Loire : « BIO »
    dict(zone=(954, 1035, 994, 1050), mode='sombre', texte='BIO', police='sans', poids='Bold', x=973, y=1042.5, cap=7.0, align='c', couleur=(40, 12, 16)),
    # Tartinable L'Atelier d'Émile
    dict(zone=(1104, 962, 1148, 985), mode='sombre', plein=True, texte=None, cap=3),
    dict(texte='Fabriqué', police='serif-it', poids='Bold', x=1125, y=969, cap=4.2, align='c', couleur=(30, 30, 30), gras=2.0),
    dict(texte='à la ferme', police='serif-it', poids='Bold', x=1125, y=978, cap=4.2, align='c', couleur=(30, 30, 30), gras=2.0),
    dict(zone=(1156, 966, 1214, 980), mode='sombre', texte="d'Émile", police='serif-it', poids='Bold', x=1185, y=973, cap=6.4, align='c', couleur=(60, 105, 72), gras=1.7),
    dict(zone=(1150, 980, 1228, 993), mode='sombre', texte='Tartinable de', police='serif', poids='SemiBold', x=1189, y=986.5, cap=4.8, align='c', couleur=(60, 60, 60), gras=1.4),
    # Sachet Maison Guinguet
    # l'étiquette est inclinée (~4°) : on ne remplace que « HOUE » par « NOIR »
    dict(zone=(1821, 1015, 1856, 1027), mode='sombre', cap=4, texte='NOIR', police='serif', poids='Medium', x=1823, y=1021.6, cap_texte=7.0, angle=4.0, align='g', couleur=(52, 36, 30)),
]
TOMATE_V10 = dict(source=(645, 884, 950, 928), cible=(889, 1011, 1054, 1035), zone=(886, 1010, 1058, 1034))

# Photo panoramique à 13 produits (resultat_gemini_v12_13produits.jpg)
CREME_TOM = (226, 214, 190)
CORRECTIONS_V12 = [
    # Rhum La Favorite
    dict(zone=(126, 694, 192, 704), mode='sombre', texte='FONDÉE EN 1842', police='sans', poids='SemiBold', x=160, y=699, cap=3.4, align='c'),
    dict(zone=(102, 768, 244, 782), mode='sombre', texte='RHUM AGRICOLE AMBRÉ', police='sans', poids='SemiBold', x=173, y=775, cap=5.6, align='c'),
    dict(zone=(108, 836, 246, 868), mode='clair', texte=None),
    dict(texte="APPELLATION D'ORIGINE CONTRÔLÉE", police='sans', poids='Medium', x=177, y=842, cap=3.3, align='c', couleur=(214, 200, 175), visible=(108, 834, 246, 870)),
    dict(texte='RÉCOLTÉ, DISTILLÉ ET MIS EN BOUTEILLE', police='sans', poids='Medium', x=177, y=852, cap=3.0, align='c', couleur=(214, 200, 175), visible=(108, 834, 246, 870)),
    dict(texte='À LA DISTILLERIE LA FAVORITE PAR LA FAMILLE DORMOY', police='sans', poids='Medium', x=177, y=861.5, cap=3.0, align='c', couleur=(214, 200, 175), visible=(108, 834, 246, 870)),
    # Jus de raisin Syrah
    dict(zone=(336, 701, 382, 712), mode='sombre', texte='CÉPAGE', police='sans', poids='SemiBold', x=358, y=706.5, cap=5.0, align='c'),
    dict(zone=(308, 745, 402, 760), mode='sombre', texte='PUR JUS DE RAISINS', police='sans', poids='SemiBold', x=355, y=753, cap=6.0, align='c'),
    dict(zone=(316, 758, 396, 768), mode='sombre', texte='SANS SUCRE AJOUTÉ*', police='sans', poids='Medium', x=355, y=763, cap=3.6, align='c'),
    # Whisky Tomatin Legacy
    dict(zone=(533, 540, 569, 554), mode='clair', texte='ESTD', police='serif', poids='SemiBold', x=551, y=547, cap=7.6, align='c', couleur=CREME_TOM),
    dict(zone=(661, 540, 702, 554), mode='clair', texte='1897', police='serif', poids='SemiBold', x=681, y=547, cap=7.6, align='c', couleur=CREME_TOM),
    dict(zone=(522, 696, 708, 722), mode='clair', texte=None, cap=3),
    dict(texte='TIME IN BOURBON BARRELS AND VIRGIN OAK CASKS BRINGS A LIGHT', police='sans', poids='Medium', x=615, y=701.7, cap=2.9, align='c', couleur=CREME_TOM),
    dict(texte='SWEETNESS TO THE TOMATIN LEGACY, WHICH BOASTS AROMAS OF', police='sans', poids='Medium', x=615, y=709.4, cap=2.9, align='c', couleur=CREME_TOM),
    dict(texte='VANILLA, WHITE CHOCOLATE AND FRESH FRUIT.', police='sans', poids='Medium', x=615, y=717.2, cap=2.9, align='c', couleur=CREME_TOM),
    # Blacailloux, Châteauneuf-du-Pape, Gragnos et Frézier : vraies étiquettes recollées (remplace_etiquette.py)
    # Sachet Maison Guinguet
    dict(zone=(1846, 894, 1882, 909), mode='sombre', cap=4, texte='NOIR', police='serif', poids='Medium', x=1848, y=901.7, cap_texte=6.4, align='g', couleur=(52, 36, 30)),
]

# Photo à 13 produits tous visibles (resultat_gemini_v14_13produits.jpg) : les étiquettes de Gragnos,
# Châteauneuf, Frézier, Blacailloux, Lutgarde, Trompe Souris, Syrah, Silure, courgettes et la plaquette
# du chocolat sont recollées en entier (remplace_etiquette.py) ; restent ces textes.
CORRECTIONS_V14 = [
    # Rhum La Favorite
    dict(zone=(118, 640, 146, 655), mode='sombre', texte=None, cap=5),
    dict(zone=(180, 640, 208, 655), mode='sombre', texte=None, cap=5),
    dict(zone=(122, 626, 204, 644), mode='sombre', texte='DISTILLERIE', police='serif', poids='Bold', arc=(163, 723.6, 89.6, 89.6, -114.4, -65.6), cap=7.6, couleur=(52, 38, 30)),
    dict(zone=(122, 704, 174, 714), mode='sombre', texte='FONDÉE EN 1842', police='sans', poids='SemiBold', x=148, y=709, cap=3.2, align='c'),
    dict(zone=(108, 764, 224, 780), mode='sombre', texte='Cœur de Canne', police='serif', poids='Bold', x=166, y=772, cap=8.4, align='c', couleur=(112, 58, 26), gras=2.0),
    dict(zone=(108, 780, 226, 790), mode='sombre', texte='RHUM AGRICOLE AMBRÉ', police='sans', poids='SemiBold', x=166, y=784.5, cap=5.0, align='c'),
    dict(zone=(156, 816, 180, 826), mode='clair', plein=True, texte='ANS', police='sans', poids='SemiBold', x=167, y=821, cap=3.6, align='c', couleur=(250, 240, 230)),
    dict(zone=(86, 845, 248, 867), mode='clair', texte=None),
    dict(texte="APPELLATION D'ORIGINE CONTRÔLÉE", police='sans', poids='Medium', x=166, y=850, cap=2.8, align='c', couleur=(214, 200, 175), visible=(86, 844, 248, 868)),
    dict(texte='RÉCOLTÉ, DISTILLÉ ET MIS EN BOUTEILLE', police='sans', poids='Medium', x=166, y=856.5, cap=2.6, align='c', couleur=(214, 200, 175), visible=(86, 844, 248, 868)),
    dict(texte='À LA DISTILLERIE LA FAVORITE PAR LA FAMILLE DORMOY', police='sans', poids='Medium', x=166, y=862.5, cap=2.6, align='c', couleur=(214, 200, 175), visible=(86, 844, 248, 868)),
    # Whisky Tomatin Legacy (le rosé passe devant à droite)
    dict(zone=(510, 571, 543, 584), mode='clair', texte='ESTD', police='serif', poids='SemiBold', x=526, y=577.5, cap=7.0, align='c', couleur=CREME_TOM),
    dict(zone=(634, 571, 664, 584), mode='clair', texte='1897', police='serif', poids='SemiBold', x=648, y=577.5, cap=7.0, align='c', couleur=CREME_TOM),
    dict(zone=(498, 629, 692, 647), mode='clair', texte='HIGHLAND SINGLE MALT', police='serif', poids='SemiBold', x=587, y=638, cap=9.6, align='c', couleur=CREME_TOM, visible=(490, 625, 692, 650)),
    dict(zone=(500, 723, 672, 752), mode='clair', texte=None, cap=3),
    dict(texte='TIME IN BOURBON BARRELS AND VIRGIN OAK CASKS BRINGS A LIGHT', police='sans', poids='Medium', x=586, y=729.5, cap=2.8, align='c', couleur=CREME_TOM),
    dict(texte='SWEETNESS TO THE TOMATIN LEGACY, WHICH BOASTS AROMAS OF', police='sans', poids='Medium', x=586, y=737.5, cap=2.8, align='c', couleur=CREME_TOM),
    dict(texte='VANILLA, WHITE CHOCOLATE AND FRESH FRUIT.', police='sans', poids='Medium', x=586, y=745.5, cap=2.8, align='c', couleur=CREME_TOM),
    dict(zone=(506, 756, 666, 771), mode='sombre', plein=True, texte='BOURBON & VIRGIN OAK CASKS', police='serif', poids='SemiBold', x=586, y=764.5, cap=6.0, align='c', couleur=(58, 44, 30)),
    dict(zone=(500, 770, 668, 790), mode='sombre', plein=True, texte=None, cap=3),
    dict(texte='DISTILLED AND BOTTLED IN SCOTLAND', police='sans', poids='Medium', x=586, y=777.5, cap=2.6, align='c', couleur=(70, 56, 40)),
    dict(texte='THE TOMATIN DISTILLERY CO LTD IV13 7YT', police='sans', poids='Medium', x=586, y=784.5, cap=2.6, align='c', couleur=(70, 56, 40)),
    dict(texte='43%', police='sans', poids='Medium', x=664, y=781, cap=3.0, align='d', couleur=(70, 56, 40)),
    dict(texte='70cl', police='sans', poids='Medium', x=506, y=781, cap=3.0, align='g', couleur=(70, 56, 40)),
    # Sachet Maison Guinguet
    dict(zone=(1782, 828, 1858, 845), mode='clair', texte='GUINGUET', police='serif', poids='Medium', x=1820, y=836.7, cap=9.0, align='c', couleur=(226, 212, 196)),
]

PHOTOS = {'v8': (CORRECTIONS_V8, TOMATE_V8), 'v10': (CORRECTIONS_V10, TOMATE_V10), 'v12': (CORRECTIONS_V12, None), 'v14': (CORRECTIONS_V14, None)}


def lum(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def effacer(img, zone, mode, cap=8, ecart=None, garde=None, plein=False):
    """Efface le texte d'une zone : les pixels de texte sont repérés par rapport au fond estimé par
    fermeture (texte sombre) ou ouverture (texte clair) morphologique, puis remplis par inpainting.
    Renvoie les pixels du texte effacé."""
    ecart = ecart or 14
    x0, y0, x1, y1 = zone
    m = 6
    X0, Y0, X1, Y1 = max(0, x0 - m), max(0, y0 - m), x1 + m, y1 + m
    reg = img[Y0:Y1, X0:X1].astype(np.uint8)
    k = int(2 * cap + 5) | 1
    noyau = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    op = cv2.MORPH_CLOSE if mode == 'sombre' else cv2.MORPH_OPEN
    fond = cv2.morphologyEx(reg, op, noyau)
    fond = cv2.GaussianBlur(fond, (0, 0), 1.5)
    L, Lf = lum(reg.astype(float)), lum(fond.astype(float))
    txt = (L < Lf - ecart) if mode == 'sombre' else (L > Lf + ecart)
    dedans = np.zeros_like(txt)
    dedans[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    if garde is not None:
        dedans &= garde[Y0:Y1, X0:X1]
    txt &= dedans
    pix = reg[txt].astype(float)
    if plein:  # zone entière (texte peu contrasté) : remplacée par le fond estimé, fondu sur les bords
        a = cv2.GaussianBlur(dedans.astype(float), (0, 0), 1.2)[..., None]
        img[Y0:Y1, X0:X1] = (reg * (1 - a) + fond * a).clip(0, 255).astype(np.uint8)
        return pix
    # remplissage par inpainting (voisins réels) : pas de halo plus clair autour des lettres
    masque = cv2.dilate(txt.astype(np.uint8) * 255, np.ones((3, 3), np.uint8), iterations=2)
    masque[~dedans] = 0
    img[Y0:Y1, X0:X1] = cv2.inpaint(reg, masque, 3, cv2.INPAINT_TELEA)
    return pix


def police(nom, poids, taille):
    f = ImageFont.truetype(str(POLICES[nom]), taille)
    try:
        f.set_variation_by_name(poids)
    except Exception:
        pass
    return f


def rendu(texte, nom, poids, cap, italique=False, angle=0.0):
    """Masque alpha du texte, à l'échelle 1, et position du haut des capitales dans ce masque."""
    taille = 200
    f = police(nom, poids, taille)
    h_cap = f.getbbox('H')[3] - f.getbbox('H')[1]
    taille = max(4, round(taille * cap * SUR / h_cap))
    f = police(nom, poids, taille)
    bb = f.getbbox(texte)
    w, h = bb[2] - bb[0] + 8 * SUR, bb[3] - bb[1] + 8 * SUR
    im = Image.new('L', (w, h), 0)
    ImageDraw.Draw(im).text((4 * SUR - bb[0], 4 * SUR - bb[1]), texte, font=f, fill=255)
    if italique:
        im = im.transform((w + h // 4, h), Image.AFFINE, (1, 0.22, -h * 0.22, 0, 1, 0), Image.BICUBIC)
    haut_cap = 4 * SUR - bb[1] + f.getbbox('H')[1]
    if angle:  # texte incliné (descend vers la droite pour un angle positif), tourné autour de son centre
        im = im.rotate(-angle, resample=Image.BICUBIC, expand=False)
    petit = im.resize((max(1, round(im.width / SUR)), max(1, round(im.height / SUR))), Image.LANCZOS)
    return np.array(petit).astype(float) / 255, haut_cap / SUR


def poser(img, alpha, gauche, haut, couleur, visible=None):
    H, W = img.shape[:2]
    h, w = alpha.shape
    x0, y0 = int(round(gauche)), int(round(haut))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    a = alpha[ya - y0:yb - y0, xa - x0:xb - x0][..., None]
    if visible:
        vx0, vy0, vx1, vy1 = visible
        clip = np.zeros_like(a)
        cx0, cy0 = max(vx0 - xa, 0), max(vy0 - ya, 0)
        cx1, cy1 = min(vx1 - xa, xb - xa), min(vy1 - ya, yb - ya)
        if cx1 > cx0 and cy1 > cy0:
            clip[cy0:cy1, cx0:cx1] = 1
        a = a * clip
    zone = img[ya:yb, xa:xb].astype(float)
    img[ya:yb, xa:xb] = (zone * (1 - a) + np.array(couleur, float) * a).clip(0, 255).astype(np.uint8)


def anneau(forme, H, W):
    """Masque de la bande entre deux ellipses (même centre), limitée verticalement : renvoie (zone, masque)."""
    cx, cy, rxi, ryi, rxo, ryo, ymin, ymax = forme
    yy, xx = np.mgrid[0:H, 0:W]
    d_in = ((xx - cx) / rxi) ** 2 + ((yy - cy) / ryi) ** 2
    d_out = ((xx - cx) / rxo) ** 2 + ((yy - cy) / ryo) ** 2
    m = (d_in > 1) & (d_out < 1) & (yy >= ymin) & (yy <= ymax)
    zone = (int(cx - rxo), int(ymin), int(cx + rxo) + 1, int(ymax) + 1)
    return zone, m


def texte_courbe(img, c):
    """Écrit un texte le long d'une ellipse, lettre par lettre (angles en degrés, y vers le bas).
    t0 -> t1 croissant : texte en haut de l'ellipse ; décroissant : texte en bas, lisible à l'endroit."""
    cx, cy, rx, ry, t0, t1 = c['arc']
    f = police(c['police'], c['poids'], 200)
    h_cap = f.getbbox('H')[3] - f.getbbox('H')[1]
    f = police(c['police'], c['poids'], max(4, round(200 * c['cap'] * SUR / h_cap)))
    avances = [f.getlength(ch) for ch in c['texte']]
    total = sum(avances)
    cumul = np.cumsum([0] + avances[:-1]) + np.array(avances) / 2
    haut = t1 > t0
    for ch, u in zip(c['texte'], cumul / total):
        if ch == ' ':
            continue
        t = np.radians(t0 + (t1 - t0) * u)
        x, y = cx + rx * np.cos(t), cy + ry * np.sin(t)
        # tangente à l'ellipse -> orientation de la lettre
        ang = np.degrees(np.arctan2(ry * np.cos(t), -rx * np.sin(t)))
        if not haut:
            ang += 180
        bb = f.getbbox(ch)
        w, h = bb[2] - bb[0] + 4 * SUR, int(h_cap * c['cap'] * SUR / h_cap * 1.6) + 4 * SUR
        im = Image.new('L', (w, h), 0)
        top_cap = f.getbbox('H')[1]
        ImageDraw.Draw(im).text((2 * SUR - bb[0], h / 2 - c['cap'] * SUR / 2 - top_cap), ch, font=f, fill=255)
        im = im.rotate(-ang, resample=Image.BICUBIC, expand=True)
        a = np.array(im.resize((max(1, round(im.width / SUR)), max(1, round(im.height / SUR))), Image.LANCZOS)).astype(float) / 255
        poser(img, a, x - a.shape[1] / 2, y - a.shape[0] / 2, c['couleur'])


def main():
    src, dst = sys.argv[1], sys.argv[2]
    CORRECTIONS, TOMATE = PHOTOS[sys.argv[3] if len(sys.argv) > 3 else 'v8']
    img = np.array(Image.open(src).convert('RGB'))
    ref = np.array(Image.open(RACINE / 'bouteilles-gemini/style-reference-terrines-chocolat.jpg').convert('RGB'))

    # 1. effacement des anciens textes (couleur du texte relevée au passage)
    couleurs = []
    for c in CORRECTIONS:
        if 'anneau' in c:
            zone, garde = anneau(c['anneau'], *img.shape[:2])
            effacer(img, zone, c['mode'], c.get('cap', 6), c.get('ecart'), garde)
            couleurs.append(None)
            continue
        if 'zone' not in c:
            couleurs.append(None)
            continue
        pix = effacer(img, c['zone'], c['mode'], c.get('cap', 6), c.get('ecart'), plein=c.get('plein', False))
        if len(pix):
            L = lum(pix)
            sel = pix[L <= np.percentile(L, 30)] if c['mode'] == 'sombre' else pix[L >= np.percentile(L, 70)]
            couleurs.append(tuple(sel.mean(axis=0)))
        else:
            couleurs.append((40, 30, 30))
    if TOMATE:
        effacer(img, TOMATE['zone'], 'sombre', 6, ecart=18)

    # 2. réécriture du vrai texte
    for c, coul in zip(CORRECTIONS, couleurs):
        if not c.get('texte'):
            continue
        if 'arc' in c:
            texte_courbe(img, c)
            continue
        cap = c.get('cap_texte', c['cap'])
        alpha, haut_cap = rendu(c['texte'], c['police'], c['poids'], cap, c.get('italique', False), c.get('angle', 0.0))
        w = alpha.shape[1]
        gauche = {'c': c['x'] - w / 2, 'g': c['x'], 'd': c['x'] - w}[c['align']]
        haut = c['y'] - cap / 2 - haut_cap
        poser(img, (alpha * c.get('gras', 1)).clip(0, 1), gauche, haut, c.get('couleur', coul), c.get('visible'))

    # 3. « à la Tomate séchée » recopié de la référence
    if not TOMATE:
        Image.fromarray(img).save(dst, quality=95)
        print(dst)
        return
    sx0, sy0, sx1, sy1 = TOMATE['source']
    rouge = ref[sy0:sy1, sx0:sx1, 0].astype(float)
    # sur la bande rouge, l'écriture se lit dans le canal rouge (bande ~200, encre ~40)
    fond = np.percentile(rouge, 90, axis=1, keepdims=True)
    a = ((fond - rouge - 25) / np.maximum(fond - 70, 1)).clip(0, 1)
    tx0, ty0, tx1, ty1 = TOMATE['cible']
    a = cv2.resize(a, (tx1 - tx0, ty1 - ty0), interpolation=cv2.INTER_AREA)
    poser(img, a, tx0, ty0, (40, 12, 16))

    Image.fromarray(img).save(dst, quality=95)
    print(dst)


if __name__ == '__main__':
    main()
