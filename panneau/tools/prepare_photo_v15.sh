#!/bin/bash
# Photo finale de l'affiche (version sombre) à partir de la photo affinée par ChatGPT (v15) :
# vraies formes de bouteilles, vraies étiquettes recollées, couleurs et textes corrigés.
# (l'agrandissement Real-ESRGAN se fait ensuite : tools/affine_photo_hd.sh)
# Usage (depuis panneau/) : bash tools/prepare_photo_v15.sh
set -e
B=bouteilles-gemini
N=$B/nouveaux-produits
REF=$B/style-reference-terrines-chocolat.jpg
T=$(mktemp -d)
R="python3 tools/remplace_etiquette.py"
C="python3 tools/retouche_couleur.py"
M="python3 tools/motif_photo.py"

# 1. formes des bouteilles redessinées par l'IA -> vraies formes (verre et reflets de la scène conservés)
#    Gragnos : bouteille bourguignonne (épaules tombantes)
ANCIENNE_BORDS="85:922:982,210:922:981,230:922:980,250:919:983,270:911:991,290:899:1004,310:888:1016,330:880:1024,350:876:1029,370:874:1031,385:872:1031" \
  python3 tools/reforme_bouteille.py $B/resultat_chatgpt_v15.png $T/0a.jpg $B/3_rouge_Chateau_de_Gragnos_Lou_Daro.jpg blanc 860 60 1045 400 375 469 375 210 0.706
#    Lutgarde : bouteille trapue à col court ; l'ancienne étiquette (trop grande, trop haute) est d'abord
#    remplacée par du verre, puis le mur laissé à nu à droite reprend sa couleur
$C $T/0a.jpg $T/0a2.jpg vertical 0 1226,539 1351,539 1351,719 1226,719
ANCIENNE_BORDS="300:1257:1321,316:1259:1320,350:1263:1315,400:1259:1320,450:1253:1326,480:1243:1338,500:1234:1343,520:1229:1348,540:1227:1350,590:1227:1350" \
  python3 tools/reforme_bouteille.py $T/0a2.jpg $T/0b1.jpg $N/biere_Lutgarde_bouteille_detouree.png detour 1205 285 1365 600 570 565 744 316
$C $T/0b1.jpg $T/0b2.jpg aplat 40 16 17 1316,466 1312,478 1314,488 1320,498 1324,508 1327,518 1328,528 1330,538 1337,548 1343,558 1347,568 1350,576 1346,576 1346,466
#    pot de courgettes : couvercle aussi haut que le vrai (le col raccourcit d'autant)
python3 tools/etire_zone.py $T/0b2.jpg $T/0b.jpg 866 1076 557:557 605:617 645:645

# 2. vraies étiquettes : photo source x0 y0 x1 y1  ->  cible x0 y0 x1 y1  [parties cachées par un produit devant]
$R $T/0b.jpg $T/1.jpg $B/3_rouge_Chateau_de_Gragnos_Lou_Daro.jpg 30 478 205 692 872 375 1031 569 860 557 1050 600
ETIRER=1 $R $T/1.jpg $T/2.jpg $B/6_champagne_Denis_Frezier_Trois_Crus.jpg 52 542 193 723 1049 512 1214 690 1040 556 1075 640 1040 640 1079 720
# Blacailloux : l'épaule du Tomatin passe devant (bord courbe)
CACHE_POLY="540,370 545,375 555,387 565,397 572,407 576,417 579,430 582,445 583,560 540,560" ETIRER=1 \
  $R $T/2.jpg $T/3.jpg $B/2_rose_Bastide_de_Blacailloux.jpg 21 375 183 628 559 349 678 557
GAIN=0.98,0.80,0.74 OVALE=1 $R $T/3.jpg $T/4.jpg $N/biere_Lutgarde_Blonde_photo.jpg 43 256 243 509 1230 564 1347 709
ETIRER=1 $R $T/4.jpg $T/5.jpg $N/biere_Trompe_Souris_Blonde_photo.jpg 25 1015 475 1678 1355 523 1469 706
ETIRER=1 $R $T/5.jpg $T/6.jpg $N/tartinable_courgettes_officiel.jpg 280 475 825 870 866 643 1077 789
# terrine Silure : étiquette entière, avec l'onglet rouge « BIO » sous la bande
$R $T/6.jpg $T/7.jpg $REF 597 690 995 960 738 657 913 776 864 630 920 800
$R $T/7.jpg $T/8.jpg $B/8_rhum_La_Favorite_Coeur_de_Canne.jpg 23 332 201 550 38 498 220 719
ETIRER=1 $R $T/8.jpg $T/9.jpg $B/1_whisky_Suntory_Toki.jpg 175 745 715 1164 248 373 398 493
$R $T/9.jpg $T/10.jpg $B/4_rouge_Chateauneuf-du-Pape_Prieure_des_Papes.jpg 27 536 204 721 671 502 851 694 733 610 870 720
# Tomatin : vrai blason (couronne, médaillon, lions), « ESTᴰ » et « 1897 », ornements de « LEGACY » :
# motifs clairs repris sur la photo du produit et peints à la couleur de l'impression
$M $T/10.jpg $T/10w.jpg $N/whisky_Tomatin_Legacy_photo.jpg 134 470 244 513 463 454 521 477 226 214 190
$M $T/10w.jpg $T/10v.jpg $N/whisky_Tomatin_Legacy_photo.jpg 79 482 132 509 433 462 462 477 226 214 190
$M $T/10v.jpg $T/10x.jpg $N/whisky_Tomatin_Legacy_photo.jpg 247 480 291 507 524 462 548 477 226 214 190
# bandeau bleu LEGACY et bande crème reconstruits proprement (texte et ornements remis ensuite)
python3 tools/reconstruit_bande.py $T/10x.jpg $T/10t.jpg 418 570 563 616 571 576 sombre uni
python3 tools/reconstruit_bande.py $T/10t.jpg $T/10u.jpg 418 616 564 649 617 648 clair
$M $T/10u.jpg $T/10y.jpg $N/whisky_Tomatin_Legacy_photo.jpg 66 646 115 664 420 579 448 589 214 200 160
$M $T/10y.jpg $T/10s.jpg $N/whisky_Tomatin_Legacy_photo.jpg 233 641 286 659 538 576 563 588 214 200 160
# « I » de TOMATIN dessiné creux par l'IA : rempli
$C $T/10s.jpg $T/10a.jpg aplat 214 200 178 543,485 547,485 547,509 543,509
# capsule du Tomatin (« The Softer Side of the Highlands », « Since 1897 », « Product of Scotland »)
$R $T/10a.jpg $T/11b.jpg $N/whisky_Tomatin_Legacy_photo.jpg 105 40 227 242 455 200 526 318
# jus de Syrah : ChatGPT a changé la forme de la bouteille (col long) -> vraie bouteille (col court, épaules
# rondes, large capsule) détourée de la photo v8, posée par-dessus, puis vraie étiquette recollée
python3 tools/colle_detoure.py $T/11b.jpg $T/11c.jpg $N/jus_Syrah_bouteille_detouree.png 216 356 0.81
ETIRER=1 $R $T/11c.jpg $T/11d.jpg $N/jus_Syrah_etiquette_complete.png 0 0 255 386 229 574 346 756
# sachet de chocolats : vrai médaillon (photo noir et blanc, fin liseré), vraie plaque « CHOCOLAT NOIR »,
# vraie rose en papier marbré
GAIN=1.0,0.95,0.92 OVALE=1 $R $T/11d.jpg $T/11e.jpg $REF 1482 643 1602 763 1499 612 1555 668
ETIRER=1 $R $T/11e.jpg $T/11f.jpg $N/chocolat_plaque_noir.png 0 0 232 38 1484 733 1578 749
GAIN=0.95,0.80,0.71 python3 tools/colle_detoure.py $T/11f.jpg $T/11g.jpg $N/chocolat_rose_detouree.png 1491 400 0.5

# 3. couleurs : rhum doré (pas rosé), purée de courgettes vert foncé, bague de la capsule du Frézier lisse
$C $T/11g.jpg $T/c1.jpg teinte 0.035 0.35 99,234 155,234 157,330 190,365 214,410 221,480 223,497 37,497 39,480 47,410 72,365 97,330
$C $T/c1.jpg $T/c2.jpg teinte 0.035 0.35 37,720 224,720 224,768 37,768
$C $T/c2.jpg $T/c3.jpg couleur 27 33 22 872,620 1070,620 1070,644 872,644
$C $T/c3.jpg $T/c4.jpg couleur 27 33 22 874,791 1066,791 1066,808 874,808
$C $T/c4.jpg $T/c5.jpg lisse 8 0.8 1091,295 1176,295 1178,316 1089,316

# 4. textes (Tomatin, capsule du Frézier) puis relief inventé sur l'épaule du Châteauneuf (la vraie est lisse)
python3 tools/corrige_textes_photo.py $T/c5.jpg $T/12.jpg v15
python3 tools/efface_relief.py $T/12.jpg $B/resultat_chatgpt_v15_corrige.jpg 721,305 811,305 823,340 835,380 843,420 847,460 847,495 681,495 681,460 681,420 693,380 705,340
if [ -n "$GARDE" ]; then echo "intermédiaires : $T"; else rm -rf $T; fi
