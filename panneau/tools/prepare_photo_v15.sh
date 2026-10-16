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
python3 tools/corrige_textes_photo.py $T/8.jpg $B/resultat_chatgpt_v15_corrige.jpg v15
rm -rf $T
