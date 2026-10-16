#!/bin/bash
# Photo finale de l'affiche (version sombre) à partir de la photo affinée par ChatGPT (v15) :
# vraies formes de bouteilles, vraies étiquettes recollées, couleurs corrigées.
# (l'agrandissement Real-ESRGAN se fait ensuite : tools/affine_photo_hd.sh)
# Usage (depuis panneau/) : bash tools/prepare_photo_v15.sh
set -e
B=bouteilles-gemini
N=$B/nouveaux-produits
REF=$B/style-reference-terrines-chocolat.jpg
T=$(mktemp -d)
R="python3 tools/remplace_etiquette.py"

# 1. formes des bouteilles redessinées par l'IA -> vraies formes (verre et reflets de la scène conservés)
#    Gragnos : bouteille bourguignonne (épaules tombantes) ; Lutgarde : bouteille trapue à col court
ANCIENNE_BORDS="85:922:982,210:922:981,230:922:980,250:919:983,270:911:991,290:899:1004,310:888:1016,330:880:1024,350:876:1029,370:874:1031,385:872:1031" \
  python3 tools/reforme_bouteille.py $B/resultat_chatgpt_v15.png $T/0a.jpg $B/3_rouge_Chateau_de_Gragnos_Lou_Daro.jpg blanc 860 60 1045 400 375 469 375 210 0.706
ANCIENNE_BORDS="300:1257:1321,316:1259:1320,350:1263:1315,400:1259:1320,450:1253:1326,480:1243:1338,500:1234:1343,520:1229:1348,540:1227:1350,590:1227:1350" \
  python3 tools/reforme_bouteille.py $T/0a.jpg $T/0b.jpg $N/biere_Lutgarde_bouteille_detouree.png detour 1205 285 1365 600 570 565 744 316

# 2. vraies étiquettes : photo source x0 y0 x1 y1  ->  cible x0 y0 x1 y1  [parties cachées par un produit devant]
$R $T/0b.jpg $T/1.jpg $B/3_rouge_Chateau_de_Gragnos_Lou_Daro.jpg 30 478 205 692 872 375 1031 569 860 557 1050 600
ETIRER=1 $R $T/1.jpg $T/2.jpg $B/6_champagne_Denis_Frezier_Trois_Crus.jpg 52 542 193 723 1049 512 1214 690 1040 556 1075 640 1040 640 1079 720
$R $T/2.jpg $T/3.jpg $B/2_rose_Bastide_de_Blacailloux.jpg 21 375 183 628 559 349 678 557 555 387 565 397 555 397 572 407 555 407 576 417 555 417 579 430 555 430 583 560
OVALE=1 $R $T/3.jpg $T/4.jpg $N/biere_Lutgarde_Blonde_photo.jpg 43 256 243 509 1228 540 1351 717
ETIRER=1 $R $T/4.jpg $T/5.jpg $N/biere_Trompe_Souris_Blonde_photo.jpg 25 1015 475 1678 1355 523 1469 706
ETIRER=1 $R $T/5.jpg $T/6.jpg $N/tartinable_courgettes_officiel.jpg 280 475 825 870 866 643 1077 789
# terrine Silure : étiquette entière, avec l'onglet rouge « BIO » sous la bande
$R $T/6.jpg $T/7.jpg $REF 597 690 995 960 738 657 913 776 864 630 920 800
$R $T/7.jpg $T/8.jpg $B/8_rhum_La_Favorite_Coeur_de_Canne.jpg 23 332 201 550 38 498 220 719
ETIRER=1 $R $T/8.jpg $T/9.jpg $B/1_whisky_Suntory_Toki.jpg 175 745 715 1164 248 373 398 493
$R $T/9.jpg $T/10.jpg $B/4_rouge_Chateauneuf-du-Pape_Prieure_des_Papes.jpg 27 536 204 721 671 502 851 694 733 610 870 720
# Tomatin : vrai blason (couronne, médaillon et lions) et vrais ornements de part et d'autre de « LEGACY »,
# repris en motif clair sur la photo du produit et peints à la couleur de l'impression
M="python3 tools/motif_photo.py"
$M $T/10.jpg $T/10x.jpg $N/whisky_Tomatin_Legacy_photo.jpg 134 470 244 513 463 454 521 477 226 214 190
$M $T/10x.jpg $T/10y.jpg $N/whisky_Tomatin_Legacy_photo.jpg 66 643 115 664 420 576 448 589 214 200 160
$M $T/10y.jpg $T/10a.jpg $N/whisky_Tomatin_Legacy_photo.jpg 233 641 286 659 538 576 563 588 214 200 160
# capsule du Tomatin (« The Softer Side of the Highlands », « Since 1897 », « Product of Scotland »)
$R $T/10a.jpg $T/11b.jpg $N/whisky_Tomatin_Legacy_photo.jpg 105 40 227 242 455 200 526 318
# jus de Syrah : ChatGPT a changé la forme de la bouteille (col long) -> vraie bouteille (col court, épaules
# rondes, large capsule) détourée de la photo v8, posée par-dessus, puis vraie étiquette recollée
python3 tools/colle_detoure.py $T/11b.jpg $T/11c.jpg $N/jus_Syrah_bouteille_detouree.png 216 356 0.81
ETIRER=1 $R $T/11c.jpg $T/11d.jpg $N/jus_Syrah_etiquette_complete.png 0 0 255 386 229 574 346 756
# sachet de chocolats : vrai médaillon (photo noir et blanc) et vraie plaque « CHOCOLAT NOIR »
OVALE=1 $R $T/11d.jpg $T/11e.jpg $REF 1491 653 1592 754 1508 620 1546 658
ETIRER=1 $R $T/11e.jpg $T/11f.jpg $REF 1440 932 1672 970 1484 733 1578 749

# 3. couleurs : rhum doré (pas rosé), purée de courgettes vert foncé, bague de la capsule du Frézier lisse
C="python3 tools/retouche_couleur.py"
$C $T/11f.jpg $T/c1.jpg teinte 0.035 0.35 99,234 155,234 157,330 190,365 214,410 221,480 223,497 37,497 39,480 47,410 72,365 97,330
$C $T/c1.jpg $T/c2.jpg teinte 0.035 0.35 37,720 224,720 224,768 37,768
$C $T/c2.jpg $T/c3.jpg couleur 27 33 22 872,609 1070,609 1070,644 872,644
$C $T/c3.jpg $T/c4.jpg couleur 27 33 22 874,791 1066,791 1066,808 874,808
$C $T/c4.jpg $T/c5.jpg lisse 8 0.8 1091,295 1176,295 1177,308 1090,308

# 4. textes (Tomatin, capsule du Frézier) puis relief inventé sur l'épaule du Châteauneuf (la vraie bouteille est lisse)
python3 tools/corrige_textes_photo.py $T/c5.jpg $T/12.jpg v15
python3 tools/efface_relief.py $T/12.jpg $B/resultat_chatgpt_v15_corrige.jpg 721,305 811,305 823,340 835,380 843,420 847,460 847,495 681,495 681,460 681,420 693,380 705,340
rm -rf $T
