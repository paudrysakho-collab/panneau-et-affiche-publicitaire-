#!/bin/bash
# Photo finale de l'affiche (version sombre) à partir de la photo affinée par ChatGPT (v15) :
# vraies étiquettes recollées et textes corrigés (l'agrandissement Real-ESRGAN se fait ensuite).
# Usage (depuis panneau/) : bash tools/prepare_photo_v15.sh
set -e
B=bouteilles-gemini
N=$B/nouveaux-produits
REF=$B/style-reference-terrines-chocolat.jpg
T=$(mktemp -d)
R="python3 tools/remplace_etiquette.py"
# photo source x0 y0 x1 y1 (étiquette réelle)  ->  cible x0 y0 x1 y1  [parties cachées par un produit devant]
$R $B/resultat_chatgpt_v15.png $T/1.jpg $B/3_rouge_Chateau_de_Gragnos_Lou_Daro.jpg 30 478 205 692 872 375 1031 569 860 553 1050 600
ETIRER=1 $R $T/1.jpg $T/2.jpg $B/6_champagne_Denis_Frezier_Trois_Crus.jpg 52 542 193 723 1049 512 1214 690 1040 556 1075 640 1040 640 1079 720
$R $T/2.jpg $T/3.jpg $B/2_rose_Bastide_de_Blacailloux.jpg 21 375 183 628 559 349 678 557 555 370 580 560
OVALE=1 $R $T/3.jpg $T/4.jpg $N/biere_Lutgarde_Blonde_photo.jpg 43 256 243 509 1228 540 1351 717
ETIRER=1 $R $T/4.jpg $T/5.jpg $N/biere_Trompe_Souris_Blonde_photo.jpg 25 1015 475 1678 1355 523 1469 706
ETIRER=1 $R $T/5.jpg $T/6.jpg $N/tartinable_courgettes_officiel.jpg 280 475 825 870 866 643 1077 789
$R $T/6.jpg $T/7.jpg $REF 597 690 995 935 738 657 913 765 864 630 920 800
ETIRER=1 $R $T/7.jpg $T/8.jpg $REF 366 482 578 868 234 558 341 728
$R $T/8.jpg $T/9.jpg $B/8_rhum_La_Favorite_Coeur_de_Canne.jpg 23 332 201 550 38 498 220 719
ETIRER=1 $R $T/9.jpg $T/10.jpg $B/1_whisky_Suntory_Toki.jpg 145 745 745 1164 247 374 411 494 247 381 328 408 250 408 326 440 246 440 330 455 242 455 335 475 236 475 340 500 397 430 415 500
$R $T/10.jpg $T/11.jpg $B/4_rouge_Chateauneuf-du-Pape_Prieure_des_Papes.jpg 27 536 204 721 671 502 851 694 733 610 870 720
# capsule du Tomatin (« The Softer Side of the Highlands », « Since 1897 », « Product of Scotland »)
$R $T/11.jpg $T/11b.jpg $N/whisky_Tomatin_Legacy_photo.jpg 105 40 227 242 455 200 526 318
python3 tools/corrige_textes_photo.py $T/11b.jpg $T/12.jpg v15
# blason et texte en relief inventés sur l'épaule du Châteauneuf (la vraie bouteille est lisse)
python3 tools/efface_relief.py $T/12.jpg $B/resultat_chatgpt_v15_corrige.jpg 721,305 811,305 823,340 835,380 843,420 847,460 847,495 681,495 681,460 681,420 693,380 705,340
rm -rf $T
