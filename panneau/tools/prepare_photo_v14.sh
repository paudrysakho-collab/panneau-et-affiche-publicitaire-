#!/bin/bash
# Photo finale de l'affiche (version sombre) à partir de la photo Gemini v14 (13 produits, tous visibles) :
# vraies étiquettes recollées, puis textes inventés corrigés.
# Usage (depuis panneau/) : bash tools/prepare_photo_v14.sh
set -e
B=bouteilles-gemini
N=$B/nouveaux-produits
REF=$B/style-reference-terrines-chocolat.jpg
T=$(mktemp -d)
R="python3 tools/remplace_etiquette.py"
# photo source x0 y0 x1 y1 (étiquette réelle)  ->  cible x0 y0 x1 y1  [parties cachées par un produit devant]
$R $B/resultat_gemini_v14_13produits.jpg $T/1.jpg $B/3_rouge_Chateau_de_Gragnos_Lou_Daro.jpg 30 478 205 692 1031 455 1221 687 1020 664 1240 700
$R $T/1.jpg $T/2.jpg $B/4_rouge_Chateauneuf-du-Pape_Prieure_des_Papes.jpg 27 536 204 721 797 609 1011 840 866 730 1020 860
ETIRER=1 $R $T/2.jpg $T/3.jpg $B/6_champagne_Denis_Frezier_Trois_Crus.jpg 52 542 193 723 1247 621 1444 830 1240 677 1286 860
$R $T/3.jpg $T/4.jpg $B/2_rose_Bastide_de_Blacailloux.jpg 21 375 183 628 664 430 798 674 660 452 703 680
OVALE=1 $R $T/4.jpg $T/5.jpg $N/biere_Lutgarde_Blonde_photo.jpg 43 256 243 509 1461 656 1611 870
ETIRER=1 $R $T/5.jpg $T/6.jpg $N/tartinable_courgettes_officiel.jpg 280 475 825 870 1024 780 1288 957
ETIRER=1 $R $T/6.jpg $T/7.jpg $REF 366 482 578 868 290 679 411 880
$R $T/7.jpg $T/8.jpg $REF 597 690 995 935 869 794 1090 930 1022 760 1100 960
ETIRER=1 $R $T/8.jpg $T/9.jpg $REF 1440 932 1672 970 1768 895 1882 917
ETIRER=1 $R $T/9.jpg $T/10.jpg $N/biere_Trompe_Souris_Blonde_photo.jpg 25 1015 475 1678 1612 634 1750 859 1742 740 1760 870
python3 tools/corrige_textes_photo.py $T/10.jpg $B/resultat_gemini_v14_final.jpg v14
cp $B/resultat_gemini_v14_final.jpg public/produits/vitrine_sombre.jpg
rm -rf $T
